from django.contrib import admin
from django.urls import path, include
from authy.views import *
from django.conf import settings
from django.conf.urls.static import static
import authy.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authy/', include('authy.urls')),
    path('profile/<str:username>/', authy.views.profile_view, name='profile'), 
    path('accounts/', include('allauth.urls')),
    path('', home, name='home'),
    path('chat/', include('chat.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
