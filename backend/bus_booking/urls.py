"""
URL configuration for bus_booking project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, IsAdminUser

doc_permission_classes = [AllowAny] if settings.DEBUG else [IsAdminUser]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path(
        'api/schema/',
        SpectacularAPIView.as_view(permission_classes=doc_permission_classes),
        name='schema',
    ),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(
            url_name='schema',
            permission_classes=doc_permission_classes,
        ),
        name='swagger-ui',
    ),

    # API v1
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/buses/', include('apps.buses.urls')),
    path('api/v1/bookings/', include('apps.bookings.urls')),
    path('api/v1/reviews/', include('apps.reviews.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
