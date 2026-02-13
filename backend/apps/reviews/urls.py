from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusReviewViewSet, OperatorReviewViewSet

router = DefaultRouter()
router.register('bus', BusReviewViewSet, basename='bus-review')
router.register('operator', OperatorReviewViewSet, basename='operator-review')

urlpatterns = [
    path('', include(router.urls)),
]
