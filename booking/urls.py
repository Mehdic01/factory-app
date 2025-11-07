from django.urls import path
from . import views

urlpatterns = [
    path("", views.booking_home, name="booking_home"),
    path("rooms/", views.booking_list, {"category": "rooms"}, name="booking_rooms"),
    path("vehicles/", views.booking_list, {"category": "cars"}, name="booking_vehicles"),
    path("rooms/new/<int:room_id>/", views.booking_room_create, name="booking_room_create"),  # NEW
]
