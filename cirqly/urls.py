from django.contrib import admin
from django.urls import path, include
from authy.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authy/', include('authy.urls')),
    path('accounts/', include('allauth.urls')),
    path('', home, name='home'),
]