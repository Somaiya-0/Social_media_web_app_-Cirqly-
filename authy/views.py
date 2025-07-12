from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, "authy/home.html")

@login_required
def logout_confirm(request):
    if request.method == "POST":
        logout(request)
        return redirect("/")
    return render(request, "authy/logout_confirm.html")