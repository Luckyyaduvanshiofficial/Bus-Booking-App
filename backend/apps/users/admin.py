from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Document, Notification


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['phone', 'name', 'role', 'is_verified', 'verification_status', 'city', 'created_at']
    list_filter = ['role', 'is_verified', 'verification_status', 'city', 'is_active', 'created_at']
    search_fields = ['phone', 'email', 'name', 'business_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'verified_at']
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Authentication', {'fields': ('id', 'phone', 'email', 'password')}),
        ('Personal Info', {'fields': ('username', 'name', 'avatar_url')}),
        ('Role & Permissions', {'fields': ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')}),
        ('Operator Info', {
            'fields': ('business_name', 'business_type', 'gst_number', 'pan_number',
                       'bank_account', 'bank_ifsc', 'bank_name', 'address', 'city'),
            'classes': ('collapse',),
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_status', 'rejection_reason', 'verified_at'),
            'classes': ('collapse',),
        }),
        ('Platform Metrics', {
            'fields': ('rating_avg', 'rating_count', 'total_bookings', 'total_buses'),
            'classes': ('collapse',),
        }),
        ('Subscription', {
            'fields': ('subscription_tier', 'subscription_expires_at', 'commission_rate'),
            'classes': ('collapse',),
        }),
        ('Settings', {'fields': ('preferred_language',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'username', 'name', 'role', 'password1', 'password2'),
        }),
    )

    actions = ['approve_operators', 'reject_operators']

    @admin.action(description='Approve selected operators')
    def approve_operators(self, request, queryset):
        queryset.filter(role='operator').update(
            is_verified=True, verification_status='verified',
        )

    @admin.action(description='Reject selected operators')
    def reject_operators(self, request, queryset):
        queryset.filter(role='operator').update(
            verification_status='rejected',
        )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'document_number', 'verification_status', 'created_at']
    list_filter = ['document_type', 'verification_status', 'created_at']
    search_fields = ['user__phone', 'user__business_name', 'document_number']
    readonly_fields = ['id', 'created_at', 'verified_at']
    list_per_page = 25

    actions = ['approve_documents']

    @admin.action(description='Approve selected documents')
    def approve_documents(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            verification_status='verified',
            verified_by=request.user,
            verified_at=timezone.now(),
        )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__phone', 'title']
    readonly_fields = ['id', 'created_at']
