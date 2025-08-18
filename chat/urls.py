from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chatlist, name="chatlist"),
    path("chat/<int:user_id>/", views.chatpage, name="chatpage"),  # use user ID
]
