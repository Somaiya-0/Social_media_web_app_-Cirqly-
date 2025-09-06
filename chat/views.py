from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q, Max
from django.contrib.auth.decorators import login_required
from .models import Message
from django.http import JsonResponse
from authy.models import Follow

@login_required
def chatlist(request):
    q = request.GET.get("q", "").strip()

    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    )

    user_ids = set()
    for msg in messages:
        if msg.sender != request.user:
            user_ids.add(msg.sender.id)
        if msg.receiver != request.user:
            user_ids.add(msg.receiver.id)

    users = User.objects.filter(id__in=user_ids)

    if q:
        users = users.filter(username__icontains=q)

    # Attach last message
    for user in users:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
        ).order_by("-timestamp").first()
        user.last_message = last_msg.text if last_msg else "No messages yet"

    # Get the user's following list (up to 4 people)
    following_list = Follow.objects.filter(follower=request.user).select_related('following')[:4]

    return render(request, "chat/chat_list.html", {
        "users": users, 
        "q": q,
        "following_list": following_list
    })

@login_required
def chatpage(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("timestamp")

    if request.GET.get("ajax") == "1":
        return JsonResponse([
            {"sender": m.sender.username, "text": m.text} for m in messages
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

    # Last messages
    last_messages = {}
    for user in users:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
        ).order_by("-timestamp").first()
        last_messages[user.id] = last_msg.text if last_msg else ""

    user_ids_pair = sorted([request.user.id, other_user.id])
    room_name = f"{user_ids_pair[0]}_{user_ids_pair[1]}"

    # Get the user's following list (up to 4 people)
    following_list = Follow.objects.filter(follower=request.user).select_related('following')[:4]

    return render(request, "chat/chat_list.html", {
        "users": users,
        "room_name": room_name,
        "messages": messages,
        "other_user": other_user,
        "last_messages": last_messages,
        "following_list": following_list,
    })