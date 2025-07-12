from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.logout_confirm, name='logout_confirm'),
]