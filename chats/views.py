from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import openai
import re
import requests
import math

from .models import Chat, Message
from .serializers import (
    ChatMessageSerializer,
    ChatResponseSerializer,
    MessageSerializer,
    ChatSerializer,
)


def more(pid):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={pid}&key={api_key}"

    response = requests.request(
        "GET",
        url,
    ).json()
    try:
        reviews = response["result"]["reviews"]
    except:
        reviews = {}

    try:
        website = response["result"]["website"]
    except:
        website = ""

    try:
        user_ratings_total = response["result"]["user_ratings_total"]
    except:
        user_ratings_total = 0

    try:
        PHOTO_REFERENCE = (
            "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference="
            + response["result"]["photos"][0]
            + api_key
        )

    except:
        PHOTO_REFERENCE = ""

    return {
        "website": website,
        "user_ratings_total": user_ratings_total,
        "reviews": reviews,
        "PHOTO_REFERENCE": PHOTO_REFERENCE,
    }


def haversine_distance(coord1, coord2):
    # Convert coordinates to radians
    lat1, lon1 = math.radians(coord1["lat"]), math.radians(coord1["lng"])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c  # Radius of Earth in kilometers

    return distance


openai.api_key = "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"


class ChatGPT(APIView):
    def post(self, request, format=None):
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            request_message = serializer.validated_data.get("message", None)
            chat_id = serializer.validated_data.get("chat_id", None)
            address = serializer.validated_data.get("address", None)
            latitude = serializer.validated_data.get("latitude", None)
            longitude = serializer.validated_data.get("longitude", None)

            if chat_id:
                chat = Chat.objects.get(id=chat_id)
            else:
                chat = Chat.objects.create()

            if not request_message:
                serializer = ChatSerializer(chat)
                return Response(serializer.data)

            user_message_obj = Message(
                content=request_message, role=Message.RoleChoices.USER, chat=chat
            )
            user_message_obj.save()

            messages = Message.objects.filter(chat=chat).order_by("timestamp")
            message_list = [
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": "The rules of conversation are ,1. Always return  a numbered  bullet list without details to any question asked 2.Only reply to questions that involve looking for help in finding services or specialist , Else reply with my primary function is to find services or specialists for you ",
                },
                {
                    "role": "assistant",
                    "content": "Sure, I can do that. Just let me know if you would like me to format any specific information in a different way. .",
                },
            ]
            for message in messages:
                role = message.role
                message_list.append({"role": role, "content": message.content})
            message_list.append(
                {
                    "role": "user",
                    "content": "Always return  a numbered  bullet list without details of specialist or services that can help or are related to my question, ",
                }
            )
            message_list.append(
                {
                    "role": "user",
                    "content": " If questions do not involve seeking a specialist or service , reply with my primary function is to find you a specialist ",
                }
            )
            message_list.append({"role": "user", "content": request_message})

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=message_list
            )

            ai_message = response.choices[0].message["content"].strip()

            # Regular expression pattern to match numbered list items
            pattern = r"^\d+\.\s+.*$"

            # Find all matches in the document
            matches = re.findall(pattern, ai_message, re.MULTILINE)

            matches = [i.split(" - ")[0] for i in matches]

            if len(matches) > 2:
                api_key = "AIzaSyDmWkVPiZKZoGSI4NHfL-GBhvOFPOFtRiY"

                def more(pid):
                    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={pid}&key={api_key}"

                    response = requests.request(
                        "GET",
                        url,
                    ).json()
                    try:
                        reviews = response["result"]["reviews"]
                    except:
                        reviews = {}

                    try:
                        website = response["result"]["website"]
                    except:
                        website = ""

                    try:
                        user_ratings_total = response["result"]["user_ratings_total"]
                    except:
                        user_ratings_total = 0

                    try:
                        PHOTO_REFERENCE = (
                            "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference="
                            + response["result"]["photos"][0]
                            + api_key
                        )

                    except:
                        PHOTO_REFERENCE = ""

                    return {
                        "website": website,
                        "user_ratings_total": user_ratings_total,
                        "reviews": reviews,
                        "PHOTO_REFERENCE": PHOTO_REFERENCE,
                    }

                address_search = matches[0] + " around " + address

                url = (
                    "https://maps.googleapis.com/maps/api/place/textsearch/json?query="
                    + address_search
                    + f"&key={api_key}"
                )

                payload = {}
                headers = {}

                response = requests.request("GET", url, headers=headers, data=payload)
                lantern = [
                    {
                        "business_name": i["name"],
                        "address": i["formatted_address"],
                        "specialty": i["types"][0],
                        "place_id": i["place_id"],
                        "rating": i["rating"],
                        "distance": round(
                            haversine_distance(
                                i["geometry"]["location"], (latitude, longitude)
                            ),
                            2,
                        ),
                    }
                    for i in response.json()["results"]
                ]
                # Key to be updated and its corresponding function
                key_to_update = "place_id"
                function_to_apply = more

                # List comprehension to add more keys by applying a function
                # updated_list_of_dicts = [{**d, 'updated_key': function_to_apply(d[key_to_update],api_key)} for d in lantern]
                updated_list_of_dicts = [
                    {**d, **function_to_apply(d[key_to_update])} for d in lantern
                ]

                updated_list_of_dicts = [
                    i for i in updated_list_of_dicts if len(i["reviews"]) > 0
                ]
                ai_messager = {"result": updated_list_of_dicts}
            else:
                ai_messager = {"result": ai_message}

            ai_message_obj = Message(
                content=ai_message, role=Message.RoleChoices.ASSISTANT, chat=chat
            )
            ai_message_obj.save()

            response_serializer = ChatResponseSerializer(data={"message": ai_messager})
            if response_serializer.is_valid():
                return Response(
                    {
                        "message": response_serializer.validated_data["message"],
                        "chat_id": chat.id,
                    }
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, chat_id=None, format=None):
        if chat_id:
            # GET method for fetching messages in a chat
            chat = Chat.objects.get(pk=chat_id)
            messages = Message.objects.filter(chat=chat).order_by("timestamp")
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        else:
            # GET method for fetching all chats
            chats = Chat.objects.all().order_by("-created_at")
            serializer = ChatSerializer(chats, many=True)
            return Response(serializer.data)
