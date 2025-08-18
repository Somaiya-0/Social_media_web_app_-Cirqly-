from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Message

@login_required
def chatlist(request):
    """Show list of users available for chatting"""
    users = User.objects.exclude(id=request.user.id)
    return render(request, "chat/chat_list.html", {"users": users})

@login_required
def chatpage(request, user_id):
    """Display chat messages between current user and selected user"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Get messages between the current user and the other user
    messages = Message.objects.filter(
        (Q(sender=request.user, receiver=other_user) |
        (Q(sender=other_user, receiver=request.user))
    )).order_by("timestamp")

    # Stable room name using sorted user IDs
    user_ids = sorted([request.user.id, other_user.id])
    room_name = f"{user_ids[0]}_{user_ids[1]}"

    return render(request, "chat/chat_room.html", {
        "other_user": other_user,
        "messages": messages,
        "room_name": room_name
    })