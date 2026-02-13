from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, PaymentViewSet, CouponViewSet, cashfree_webhook

router = DefaultRouter()
# Register specific prefixes BEFORE the catch-all '' prefix
# so 'coupons/' and 'payments/' match before BookingViewSet's detail route
router.register('payments', PaymentViewSet, basename='payment')
router.register('coupons', CouponViewSet, basename='coupon')
router.register('', BookingViewSet, basename='booking')

urlpatterns = [
    # Cashfree webhook — unauthenticated, HMAC-verified
    path('payments/webhook/', cashfree_webhook, name='cashfree-webhook'),
    path('', include(router.urls)),
]
