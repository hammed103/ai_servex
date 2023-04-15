from rest_framework import serializers

from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class ChatMessageSerializer(serializers.Serializer):
    chat_id = serializers.UUIDField(required=False)
    message = serializers.CharField(required=False)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    address = serializers.CharField(required=False)


class ChatResponseSerializer(serializers.Serializer):
    message = serializers.DictField()
