from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.logout_confirm, name='logout_confirm'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
]