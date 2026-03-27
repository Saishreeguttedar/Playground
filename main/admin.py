from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("booking_id", "user", "source", "destination", "date", "price", "status")
    search_fields = ("booking_id", "user__username", "source", "destination")
    list_filter = ("status", "date", "created_at")
