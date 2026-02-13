from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, PaymentViewSet, CouponViewSet

router = DefaultRouter()
# Register specific prefixes BEFORE the catch-all '' prefix
# so 'coupons/' and 'payments/' match before BookingViewSet's detail route
router.register('payments', PaymentViewSet, basename='payment')
router.register('coupons', CouponViewSet, basename='coupon')
router.register('', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]
