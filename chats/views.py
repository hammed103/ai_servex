from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import openai
import re


from .models import Chat, Message
from .serializers import (
    ChatMessageSerializer,
    ChatResponseSerializer,
    MessageSerializer,
    ChatSerializer,
)

openai.api_key = "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"


class ChatGPT(APIView):
    def post(self, request, format=None):
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            request_message = serializer.validated_data.get("message", None)
            chat_id = serializer.validated_data.get("chat_id", None)

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
                ai_message = "\n".join(matches)

            ai_message_obj = Message(
                content=ai_message, role=Message.RoleChoices.ASSISTANT, chat=chat
            )
            ai_message_obj.save()

            response_serializer = ChatResponseSerializer(data={"message": ai_message})
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
