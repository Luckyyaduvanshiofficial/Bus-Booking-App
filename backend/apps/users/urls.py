from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, OperatorViewSet, DocumentViewSet,
    NotificationViewSet,
    send_otp, verify_otp, register,
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('operators', OperatorViewSet, basename='operator')
router.register('documents', DocumentViewSet, basename='document')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Auth endpoints
    path('auth/send-otp/', send_otp, name='send-otp'),
    path('auth/verify-otp/', verify_otp, name='verify-otp'),
    path('auth/register/', register, name='register'),
    # ViewSet routes
    path('', include(router.urls)),
]
