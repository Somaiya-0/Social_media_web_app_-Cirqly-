from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_confirm, name='logout_confirm'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('search/', views.search_users, name='search_users'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('create-post/', views.create_post, name='create_post'),
    path("edit_post/", views.edit_post, name="edit_post"),
    path('delete_post/', views.delete_post, name='delete_post'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('like/', views.like_post, name='like_post'),
    path('add_comment/', views.add_comment, name='add_comment'),
    path('delete_comment/', views.delete_comment, name='delete_comment'),
    path('notifications/', views.notifications_view, name='notifications_view'),
    
]
