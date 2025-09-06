import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        # Personal channel for sidebar updates
        self.personal_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.personal_group_name, self.channel_name)

        # Room channel if joining a chat room
        self.room_name = self.scope["url_route"]["kwargs"].get("room_name")
        if self.room_name:
            self.room_group_name = f"chat_{self.room_name}"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave personal group
        await self.channel_layer.group_discard(self.personal_group_name, self.channel_name)

        # Leave room group if exists
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "").strip()
        if not message:
            return

        sender = self.user

        # Determine the receiver from room_name
        if not self.room_name:
            return
        user_ids = [int(x) for x in self.room_name.split("_")]
        receiver_id = user_ids[0] if sender.id == user_ids[1] else user_ids[1]
        receiver = await self.get_user(receiver_id)

        # Save message
        await self.save_message(sender, receiver, message)

        # --- Send message to chat room only ---
        room_event = {
            "type": "chat_message",
            "message": message,
            "username": sender.username,
            "sender_id": sender.id,
            "receiver_id": receiver.id,
        }
        correct_room = f"chat_{min(sender.id, receiver.id)}_{max(sender.id, receiver.id)}"
        await self.channel_layer.group_send(correct_room, room_event)

        # --- Send sidebar update only ---
        sidebar_event = {
            "type": "sidebar_update",
            "message": message,
            "sender_id": sender.id,
            "receiver_id": receiver.id,
            "username": sender.username,
        }
        await self.channel_layer.group_send(f"user_{receiver.id}", sidebar_event)

    # --- Handle chat log messages ---
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # --- Handle sidebar updates ---
    async def sidebar_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, sender, receiver, text):
        return Message.objects.create(sender=sender, receiver=receiver, text=text)

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)
