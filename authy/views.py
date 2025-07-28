from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import ProfileUpdateForm

@login_required
def home(request):
    return render(request, "authy/home.html")

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



@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile

    if request.method == "POST" and request.user == user:
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
