from django.contrib import admin
from .models import Booking, Payment, BookingHistory, Coupon, CouponUsage


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['id', 'cf_order_id', 'cf_payment_id', 'created_at']


class BookingHistoryInline(admin.TabularInline):
    model = BookingHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'reason', 'created_by', 'created_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_number', 'customer', 'operator', 'bus',
        'pickup_date', 'status', 'payment_status',
        'total_amount', 'created_at',
    ]
    list_filter = ['status', 'payment_status', 'trip_type', 'payment_mode', 'pickup_date', 'created_at']
    search_fields = ['booking_number', 'customer__phone', 'operator__business_name', 'bus__name']
    readonly_fields = [
        'id', 'booking_number', 'commission_rate', 'commission_amount',
        'operator_payout', 'platform_fee', 'created_at', 'updated_at',
    ]
    list_per_page = 25
    inlines = [PaymentInline, BookingHistoryInline]

    fieldsets = (
        ('Booking Info', {
            'fields': ('id', 'booking_number', 'customer', 'operator', 'bus', 'trip_type'),
        }),
        ('Trip Details', {
            'fields': (
                'pickup_location', 'pickup_lat', 'pickup_lng',
                'drop_location', 'drop_lat', 'drop_lng',
                'pickup_date', 'pickup_time', 'return_date',
                'passenger_count', 'purpose', 'special_requests',
                'estimated_km', 'estimated_route',
            ),
        }),
        ('Pricing Breakdown', {
            'fields': (
                'base_amount', 'driver_charge', 'night_charge',
                'toll_estimate', 'platform_fee', 'discount_amount',
                'total_amount',
            ),
            'classes': ('collapse',),
        }),
        ('Commission', {
            'fields': ('commission_rate', 'commission_amount', 'operator_payout'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': (
                'status', 'payment_status', 'payment_mode', 'advance_amount',
                'operator_response', 'operator_response_at', 'rejection_reason',
                'operator_payout_status', 'operator_payout_at',
            ),
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason', 'cancelled_at', 'refund_amount'),
            'classes': ('collapse',),
        }),
        ('Completion', {'fields': ('completed_at',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'booking', 'amount', 'payment_type', 'payment_method',
        'status', 'created_at',
    ]
    list_filter = ['status', 'payment_type', 'payment_method', 'created_at']
    search_fields = ['booking__booking_number', 'cf_order_id', 'cf_payment_id']
    readonly_fields = ['id', 'created_at']
    list_per_page = 25


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ['booking', 'old_status', 'new_status', 'created_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['booking__booking_number']
    readonly_fields = ['id', 'created_at']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_type', 'discount_value', 'max_discount',
        'usage_limit', 'used_count', 'is_active', 'valid_until',
    ]
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code', 'description']
    readonly_fields = ['id', 'used_count', 'created_at']
    list_per_page = 25


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'booking', 'discount_applied', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['id', 'created_at']
