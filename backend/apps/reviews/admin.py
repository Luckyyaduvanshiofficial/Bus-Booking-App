from django.contrib import admin, messages
from .models import BusReview, OperatorReview
from .services import ReviewService


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
        approved = 0
        for review in queryset.select_related('bus', 'operator'):
            ReviewService.moderate_review(review=review, action='approve')
            approved += 1
        self.message_user(
            request,
            f'Approved {approved} review(s).',
            level=messages.SUCCESS,
        )

    @admin.action(description='Flag selected reviews')
    def flag_reviews(self, request, queryset):
        flagged = 0
        for review in queryset.select_related('bus', 'operator'):
            ReviewService.moderate_review(review=review, action='flag')
            flagged += 1
        self.message_user(
            request,
            f'Flagged {flagged} review(s).',
            level=messages.WARNING,
        )


@admin.register(OperatorReview)
class OperatorReviewAdmin(admin.ModelAdmin):
    list_display = ['operator', 'reviewer', 'overall_rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'overall_rating', 'created_at']
    search_fields = ['operator__business_name', 'reviewer__phone']
    readonly_fields = ['id', 'overall_rating', 'created_at', 'updated_at']
