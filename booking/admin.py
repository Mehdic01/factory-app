from django.contrib import admin
from .models import Room, Booking

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "size", "category", "capacity", "location")
    list_filter = ("size", "category")
    search_fields = ("name", "location")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "start_at", "end_at", "title")
    list_filter = ("room",)
    search_fields = ("room__name", "user__username", "title")
