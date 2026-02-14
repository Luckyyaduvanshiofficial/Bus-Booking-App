from django.contrib import admin, messages
from .models import Bus, BusPhoto, BusAmenity, AvailabilityBlock
from .services import BusService


class BusPhotoInline(admin.TabularInline):
    model = BusPhoto
    extra = 1
    fields = ['photo_url', 'photo_type', 'display_order', 'is_primary']


class BusAmenityInline(admin.TabularInline):
    model = BusAmenity
    extra = 1


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'operator', 'registration_number', 'bus_type',
        'seating_capacity', 'price_per_km', 'base_city',
        'is_approved', 'approval_status', 'is_active', 'created_at',
    ]
    list_filter = [
        'bus_type', 'ac_type', 'fuel_type', 'base_city',
        'approval_status', 'is_active', 'created_at',
    ]
    search_fields = ['name', 'registration_number', 'operator__business_name', 'base_city']
    readonly_fields = ['id', 'created_at', 'updated_at', 'rating_avg', 'rating_count', 'total_trips']
    list_per_page = 25
    inlines = [BusPhotoInline, BusAmenityInline]

    fieldsets = (
        ('Basic Info', {'fields': ('id', 'operator', 'name', 'description', 'bus_type')}),
        ('Capacity', {'fields': ('seating_capacity',)}),
        ('Vehicle Details', {
            'fields': ('registration_number', 'make_model', 'manufacture_year', 'ac_type', 'fuel_type'),
        }),
        ('Pricing', {'fields': ('price_per_km', 'base_price', 'driver_charge', 'night_charge')}),
        ('Location', {'fields': ('base_city', 'base_area')}),
        ('Approval', {'fields': ('approval_status',)}),
        ('Ratings', {
            'fields': ('rating_avg', 'rating_count', 'total_trips'),
            'classes': ('collapse',),
        }),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    actions = ['approve_buses', 'reject_buses']

    @admin.action(description='Approve selected buses')
    def approve_buses(self, request, queryset):
        approved = 0
        for bus in queryset.select_related('operator'):
            BusService.approve_bus(bus=bus, action='approve')
            approved += 1
        self.message_user(
            request,
            f'Approved {approved} bus(es).',
            level=messages.SUCCESS,
        )

    @admin.action(description='Reject selected buses')
    def reject_buses(self, request, queryset):
        rejected = 0
        for bus in queryset.select_related('operator'):
            BusService.approve_bus(bus=bus, action='reject')
            rejected += 1
        self.message_user(
            request,
            f'Rejected {rejected} bus(es).',
            level=messages.WARNING,
        )


@admin.register(BusPhoto)
class BusPhotoAdmin(admin.ModelAdmin):
    list_display = ['bus', 'photo_type', 'display_order', 'is_primary', 'created_at']
    list_filter = ['photo_type', 'is_primary']
    search_fields = ['bus__name']


@admin.register(BusAmenity)
class BusAmenityAdmin(admin.ModelAdmin):
    list_display = ['bus', 'amenity']
    list_filter = ['amenity']
    search_fields = ['bus__name']


@admin.register(AvailabilityBlock)
class AvailabilityBlockAdmin(admin.ModelAdmin):
    list_display = ['bus', 'blocked_date', 'block_reason', 'booking', 'created_at']
    list_filter = ['block_reason', 'blocked_date']
    search_fields = ['bus__name']
    readonly_fields = ['id', 'created_at']
