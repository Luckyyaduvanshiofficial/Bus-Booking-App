from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusViewSet, BusPhotoViewSet, BusAmenityViewSet, AvailabilityBlockViewSet

router = DefaultRouter()
router.register('', BusViewSet, basename='bus')

# Nested routes – use UUID for bus_id
urlpatterns = [
    path('', include(router.urls)),
    path(
        '<uuid:bus_id>/photos/',
        BusPhotoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='bus-photos',
    ),
    path(
        '<uuid:bus_id>/photos/<uuid:pk>/',
        BusPhotoViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
        name='bus-photo-detail',
    ),
    path(
        '<uuid:bus_id>/amenities/',
        BusAmenityViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='bus-amenities',
    ),
    path(
        '<uuid:bus_id>/amenities/<uuid:pk>/',
        BusAmenityViewSet.as_view({'delete': 'destroy'}),
        name='bus-amenity-detail',
    ),
    path(
        '<uuid:bus_id>/availability-blocks/',
        AvailabilityBlockViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='bus-availability-blocks',
    ),
    path(
        '<uuid:bus_id>/availability-blocks/<uuid:pk>/',
        AvailabilityBlockViewSet.as_view({'delete': 'destroy'}),
        name='bus-availability-block-detail',
    ),
]
