from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Post,Profile,Follow,Comment,Notification
from .forms import PostForm
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q  # Add this import
import json

@login_required
def home(request):
    # Get users you're following
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    posts = Post.objects.filter(
        Q(user__id__in=following_users) | Q(user=request.user)
    ).order_by('-created_at')
    
    # If no posts (not following anyone and no own posts), show random posts
    if not posts.exists():
    # Get random users (excluding yourself)
        random_users = list(User.objects.exclude(id=request.user.id).order_by('?')[:5])
        if random_users:
            random_user_ids = [u.id for u in random_users]  # convert to list of IDs
            # Get posts from these random users
            posts = Post.objects.filter(
                user__in=random_user_ids
            ).order_by('-created_at')[:10] # Limit to 10 random posts
    
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    following_list = Follow.objects.filter(follower=request.user).select_related('following')[:4]

    context = {
        "posts": posts,
        "unread_count": unread_count,
        "following_users": following_users,   
        "following_list": following_list,
    }
    return render(request, "authy/home.html", context)




@login_required
def logout_confirm(request):
    if request.method == "POST":
        logout(request)
        return redirect("/")
    return render(request, "authy/logout_confirm.html")



@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=profile_user)

    # --- Handle POST updates ---
    if request.method == "POST" and request.user == profile_user:
        # Bio update
        new_bio = request.POST.get("bio")
        if new_bio is not None:
            profile.bio = new_bio.strip()
            profile.save()
            return redirect("profile", username=profile_user.username)

        # Profile picture update
        if "image" in request.FILES:
            profile.image = request.FILES["image"]
            profile.save()
            return redirect("profile", username=profile_user.username)

    # --- GET request (normal profile view) ---
    is_following = Follow.objects.filter(
        follower=request.user,
        following=profile_user
    ).exists()

    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()

    posts = profile_user.posts.order_by('-created_at')

    context = {
        "profile_user": profile_user,
        "profile": profile,
        "is_following": is_following,
        "followers_count": followers_count,
        "following_count": following_count,
        "posts": posts,
    }
    return render(request, "account/profile.html", context)




@login_required
def search_users(request):
    """Full-page search results (HTML)"""
    query = request.GET.get('q', '').strip()
    users = User.objects.none()
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
    return render(request, "authy/search_results.html", {"users": users, "query": query})


@login_required
def search_suggest(request):
    """Live suggestions (JSON)"""
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)[:5]
        for u in users:
            img_url = getattr(getattr(u, 'profile', None), 'image', None)
            if img_url:
                img_url = img_url.url
            else:
                img_url = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"

            results.append({
                "username": u.username,
                "full_name": u.get_full_name(),
                "profile_url": f"/profile/{u.username}/",
                "profile_image": img_url
            })
    return JsonResponse({"users": results})


@login_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get("content")
        post_image = request.FILES.get("post_image")  # get uploaded file

        post = Post.objects.create(
            user=request.user,
            content=content,
            post_image=post_image  # save file to model
        )
        # Redirect to the profile page of the logged-in user
        return redirect('profile', username=request.user.username)
    
    return redirect('profile', username=request.user.username)




@login_required
@csrf_exempt
def delete_post(request):
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        try:
            post = Post.objects.get(id=post_id, user=request.user)
            post.delete()
            return JsonResponse({"success": True})
        except Post.DoesNotExist:
            return JsonResponse({"success": False, "error": "Post not found"})
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def follow_user(request, username):
    target_user = get_object_or_404(User, username=username)

    if request.user != target_user:
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        if created:
            # New follow -> create notification
            Notification.objects.create(
                sender=request.user,
                recipient=target_user,
                notification_type="follow"
            )
        else:
            # Unfollow -> delete the follow notification
            follow.delete()
            Notification.objects.filter(
                sender=request.user,
                recipient=target_user,
                notification_type="follow"
            ).delete()

    return redirect('profile', username=target_user.username)


@login_required
@require_POST
def like_post(request):
    post_id = request.POST.get('post_id')
    post = Post.objects.get(id=post_id)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
        # delete notification if unliked
        Notification.objects.filter(
            sender=request.user,
            recipient=post.user,
            notification_type="like",
            post=post
        ).delete()
    else:
        post.likes.add(request.user)
        liked = True
        if request.user != post.user:
            Notification.objects.create(
                sender=request.user,
                recipient=post.user,
                notification_type="like",
                post=post
            )

    return JsonResponse({'liked': liked, 'total_likes': post.total_likes()})


@login_required
@require_POST
def add_comment(request):
    post_id = request.POST.get('post_id')
    content = request.POST.get('content')
    post = get_object_or_404(Post, id=post_id)

    comment = Comment.objects.create(
        user=request.user,
        post=post,
        content=content
    )

    # create notification (only if commenting on someone else's post)
    if request.user != post.user:
        Notification.objects.create(
            sender=request.user,
            recipient=post.user,
            notification_type="comment",
            post=post,
            comment=comment
        )

    profile_image_url = ''
    if hasattr(request.user, 'profile') and request.user.profile.image:
        profile_image_url = request.user.profile.image.url

    return JsonResponse({
    'success': True,
    'comment_id': comment.id,
    'username': request.user.username,
    'content': comment.content,
    'user_profile_image': profile_image_url,
    'total_comments': post.comments.count()
})


@login_required
@require_POST
@csrf_exempt
def delete_comment(request):
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.user == request.user:
            post_id = comment.post.id
            comment.delete()
            return JsonResponse({'success': True, 'post_id': post_id})
        else:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all().order_by('-created_at')

    # Mark unread ones as read
    request.user.notifications.filter(is_read=False).update(is_read=True)

    return render(request, "authy/notifications.html", {"notifications": notifications})
