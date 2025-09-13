"""
URL configuration for farmacia_estoque project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('users/', include('users.urls')),
    path('inventory/', include('inventory.urls')),
    
    # Redirects for convenience
    path('login/', lambda request: redirect('users:login')),
    path('logout/', lambda request: redirect('users:logout')),
    path('dashboard/', lambda request: redirect('core:dashboard')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
