from django.contrib import admin
from .models import BusReview, OperatorReview


@admin.register(BusReview)
class BusReviewAdmin(admin.ModelAdmin):
    list_display = [
        'bus', 'customer', 'rating_overall',
        'is_approved', 'is_flagged', 'created_at',
    ]
    list_filter = ['is_approved', 'is_flagged', 'rating_overall', 'created_at']
    search_fields = ['bus__name', 'customer__phone', 'review_text']
    readonly_fields = ['id', 'created_at']
    list_per_page = 25

    actions = ['approve_reviews', 'flag_reviews']

    @admin.action(description='Approve selected reviews')
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True, is_flagged=False)

    @admin.action(description='Flag selected reviews')
    def flag_reviews(self, request, queryset):
        queryset.update(is_flagged=True)


@admin.register(OperatorReview)
class OperatorReviewAdmin(admin.ModelAdmin):
    list_display = ['operator', 'reviewer', 'overall_rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'overall_rating', 'created_at']
    search_fields = ['operator__business_name', 'reviewer__phone']
    readonly_fields = ['id', 'overall_rating', 'created_at', 'updated_at']
