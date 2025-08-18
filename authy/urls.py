from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.logout_confirm, name='logout_confirm'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    # full-page search (HTML)
    path('search/', views.search_users, name='search_users'),
    # live suggestions (JSON only)
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('create-post/', views.create_post, name='create_post'),
    # urls.py
    path('follow/<str:username>/', views.follow_user, name='follow_user')

]
