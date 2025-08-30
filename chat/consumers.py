import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        if not message:
            return

        sender = self.scope['user']

        # Extract user IDs from room name
        user_ids = [int(x) for x in self.room_name.split("_")]
        receiver_id = user_ids[0] if sender.id == user_ids[1] else user_ids[1]
        receiver = await self.get_user(receiver_id)

        # Save message to DB
        await self.save_message(sender, receiver, message)

        # Broadcast message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': sender.username,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
        }))

    # --- DB helpers ---
    @database_sync_to_async
    def save_message(self, sender, receiver, text):
        return Message.objects.create(sender=sender, receiver=receiver, text=text)

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)
