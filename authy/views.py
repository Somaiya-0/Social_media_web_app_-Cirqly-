from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Post,Profile,Follow
from .forms import PostForm
from django.views.decorators.http import require_POST

@login_required
def home(request):
    # Get all users except current user
    users = User.objects.exclude(id=request.user.id)
    
    # Get the users that the current user is following
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    
    # Get posts from users the current user is following
    posts = Post.objects.filter(user__id__in=following_users).order_by('-created_at')
    
    context = {
        "users": users,
        "posts": posts,
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

    # check if logged in user is already following this profile_user
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
    if request.method == 'POST':
        content = request.POST.get('content')   # matches PostForm + Post model
        image = request.FILES.get('post_image') # matches PostForm + Post model

        new_post = Post.objects.create(
            user=request.user,   # use FK, not username string
            content=content,
            post_image=image
        )
        new_post.save()

    return redirect('profile', username=request.user.username)




@login_required
def follow_user(request, username):
    target_user = get_object_or_404(User, username=username)

    if request.user != target_user:  # prevent following self
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        if not created:
            # Already following -> unfollow
            follow.delete()

    return redirect('profile', username=target_user.username)


@login_required
@require_POST
def like_post(request):
    post_id = request.POST.get('post_id')
    post = Post.objects.get(id=post_id)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({'liked': liked, 'total_likes': post.total_likes()})