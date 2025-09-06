from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Message
from django.http import JsonResponse
from authy.models import Follow
from datetime import datetime, timezone


@login_required
def chatlist(request):
    """
    Sidebar + search endpoint
    - Default: users you've chatted with
    - Search (?q=...): all users matching query
    """
    q = request.GET.get("q", "").strip()

    if q:
        # Search all users except current user
            users = User.objects.exclude(id=request.user.id).exclude(is_superuser=True).filter(username__icontains=q)

    else:
        # Default sidebar: users you've chatted with
        messages = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
        user_ids = set()
        for msg in messages:
            if msg.sender != request.user:
                user_ids.add(msg.sender.id)
            if msg.receiver != request.user:
                user_ids.add(msg.receiver.id)
        users = User.objects.filter(id__in=user_ids)

    # Attach last message and timestamp
    user_data = []
    for user in users:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
        ).order_by("-timestamp").first()
        user.last_message = last_msg.text if last_msg else "No messages yet"
        user.last_message_time = last_msg.timestamp if last_msg else None
        user_data.append(user)

    # Sort by last message time
    user_data.sort(key=lambda x: x.last_message_time or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # AJAX request → return JSON for dynamic search
    if request.GET.get("ajax") == "1":
        return JsonResponse([
            {
                "id": user.id,
                "username": user.username,
                "last_message": user.last_message,
                "last_message_time": int(user.last_message_time.timestamp()) if user.last_message_time else 0,
                "avatar": user.profile.image.url if hasattr(user, 'profile') and user.profile.image else
                          "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"
            } for user in user_data
        ], safe=False)

    # Sidebar suggestions
    following_list = Follow.objects.filter(follower=request.user).select_related("following")[:4]

    return render(request, "chat/chat_list.html", {
        "users": user_data,
        "q": q,
        "following_list": following_list
    })


@login_required
def chatpage(request, user_id):
    """
    Renders chat room with a specific user.
    Supports AJAX for loading messages.
    """
    other_user = get_object_or_404(User, id=user_id)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by("timestamp")

    if request.GET.get("ajax") == "1":
        return JsonResponse([
            {"sender": m.sender.username, "sender_id": m.sender.id, "text": m.text} for m in messages
        ], safe=False)

    # Sidebar users
    all_messages = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
    user_ids = set()
    for msg in all_messages:
        if msg.sender != request.user:
            user_ids.add(msg.sender.id)
        if msg.receiver != request.user:
            user_ids.add(msg.receiver.id)
    users = User.objects.filter(id__in=user_ids)

    # Last messages for sidebar
    last_messages = {}
    for user in users:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
        ).order_by("-timestamp").first()
        last_messages[user.id] = last_msg.text if last_msg else ""

    # Room name
    user_ids_pair = sorted([request.user.id, other_user.id])
    room_name = f"{user_ids_pair[0]}_{user_ids_pair[1]}"

    # Sidebar suggestions
    following_list = Follow.objects.filter(follower=request.user).select_related("following")[:4]

    return render(request, "chat/chat_list.html", {
        "users": users,
        "room_name": room_name,
        "messages": messages,
        "other_user": other_user,
        "last_messages": last_messages,
        "following_list": following_list
    })
