from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import ProfileUpdateForm
from django.http import JsonResponse
from .models import Post
from .forms import PostForm

@login_required
def home(request):
    users = User.objects.exclude(id=request.user.id)  # everyone except current user
    return render(request, "authy/home.html", {"users": users})

@login_required
def logout_confirm(request):
    if request.method == "POST":
        logout(request)
        return redirect("/")
    return render(request, "authy/logout_confirm.html")

# @login_required
# def profile_view(request, username):
#     user = get_object_or_404(User, username=username)
#     profile = user.profile

#     if request.method == "POST" and request.user == user:
#         bio = request.POST.get('bio', '')
#         profile.bio = bio
#         profile.save()
        
#         return redirect('profile', username=user.username)

#     return render(request, "account/profile.html", {
#         "profile_user": user,
#         "profile": profile,
#     })



# @login_required
# def profile_view(request, username):
#     user = get_object_or_404(User, username=username)
#     profile = user.profile

#     if request.method == "POST" and request.user == user:
#         form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect('profile', username=user.username)
#     else:
#         form = ProfileUpdateForm(instance=profile)

#     return render(request, "account/profile.html", {
#         "profile_user": user,
#         "profile": profile,
#         "form": form,
#     })



@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile

    # Only handle profile update (image/bio)
    if request.method == "POST" and request.user == user and 'image' in request.FILES or 'bio' in request.POST:
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=user.username)
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, "account/profile.html", {
        "profile_user": user,
        "profile": profile,
        "form": form,
    })



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


def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    # do follow logic here
    return redirect('profile', username=username)