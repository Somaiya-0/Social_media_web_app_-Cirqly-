from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Message
from django.http import JsonResponse
from authy.models import Follow
from django.utils import timezone
from datetime import datetime


@login_required
def chatlist(request):
    q = request.GET.get("q", "").strip()

    # All messages where the user is either sender or receiver
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    )

    # Collect IDs of all users the current user has chatted with
    user_ids = set()
    for msg in messages:
        if msg.sender != request.user:
            user_ids.add(msg.sender.id)
        if msg.receiver != request.user:
            user_ids.add(msg.receiver.id)

    users = User.objects.filter(id__in=user_ids)

    # Search filter
    if q:
        users = users.filter(username__icontains=q)

    # Attach last message and timestamp to each user
    user_data = []
    for user in users:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=user) |
            Q(sender=user, receiver=request.user)
        ).order_by("-timestamp").first()

        user.last_message = last_msg.text if last_msg else "No messages yet"
        user.last_message_time = last_msg.timestamp if last_msg else None
        user_data.append(user)

    # Sort users by most recent activity
    user_data.sort(
        key=lambda x: x.last_message_time or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )

    # Get following list (up to 4 users for sidebar)
    following_list = Follow.objects.filter(
        follower=request.user
    ).select_related("following")[:4]

    return render(request, "chat/chat_list.html", {
        "users": user_data,
        "q": q,
        "following_list": following_list
    })


@login_required
def chatpage(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    # All messages between current user and the other user
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("timestamp")

    # If AJAX, return JSON (used when clicking on a chat in the sidebar)
    if request.GET.get("ajax") == "1":
        return JsonResponse([
            {
                "sender": m.sender.username,
                "sender_id": m.sender.id,   # ✅ include sender_id
                "text": m.text
            } for m in messages
        ], safe=False)

    # Sidebar users
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    )
    user_ids = set()
    for msg in all_messages:
        if msg.sender != request.user:
            user_ids.add(msg.sender.id)
        if msg.receiver != request.user:
            user_ids.add(msg.receiver.id)
    users = User.objects.filter(id__in=user_ids)

    # Last messages for sidebar preview
    last_messages = {}
    for user in users:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=user) |
            Q(sender=user, receiver=request.user)
        ).order_by("-timestamp").first()
        last_messages[user.id] = last_msg.text if last_msg else ""

    # Room name (consistent ordering of user IDs)
    user_ids_pair = sorted([request.user.id, other_user.id])
    room_name = f"{user_ids_pair[0]}_{user_ids_pair[1]}"

    # Following list (sidebar suggestion)
    following_list = Follow.objects.filter(
        follower=request.user
    ).select_related("following")[:4]

    return render(request, "chat/chat_list.html", {
        "users": users,
        "room_name": room_name,
        "messages": messages,
        "other_user": other_user,
        "last_messages": last_messages,
        "following_list": following_list,
    })
