# booking/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Room, RoomSize, RoomCategory
from .forms import BookingSearchForm, BookingCreateForm
from django.utils import timezone
from datetime import date as date_cls  


@login_required
def booking_home(request):
    return redirect("booking_rooms")

@login_required
def booking_list(request, category):
    category = (category or "rooms").lower()

    results = []
    size_options = []
    room_category_options = []

    if category == "rooms":
        form = BookingSearchForm(request.GET or None)
        valid = form.is_valid()
        data = form.cleaned_data if valid else {}

        qs = Room.objects.all()
        size = data.get("size") or ""
        room_cat = data.get("room_category") or ""
        if size:
            qs = qs.filter(size=size)
        if room_cat:
            qs = qs.filter(category=room_cat)

        start_dt = data.get("start_dt")
        end_dt = data.get("end_dt")
        if start_dt and end_dt and start_dt < end_dt:
            qs = qs.exclude(bookings__start_at__lt=end_dt, bookings__end_at__gt=start_dt)

        results = list(qs.order_by("name")[:50])
        size_options = list(RoomSize.choices)
        room_category_options = list(RoomCategory.choices)
    else:
        form = None  # vehicles not implemented yet

    # Default date shown in the UI = today if not provided
    today = timezone.localdate()
    date_str = request.GET.get("date") or today.isoformat()

    try:
        chosen_date = date_cls.fromisoformat(date_str)
        
    except ValueError:
        messages.error(request, "Invalid date format. Using today's date.")
        params = request.GET.copy()
        params["date"] = today.isoformat()
        return redirect(f"{request.path}?{params.urlencode()}")
    if chosen_date < today:
        messages.error(request, "Date cannot be in the past. Using today's date.")
        params = request.GET.copy()
        params["date"] = today.isoformat()
        return redirect(f"{request.path}?{params.urlencode()}")
        

    return render(request, "booking/booking_list.html", {
        "active": "res",
        "category": category,
        "form": form,
        "date": date_str,  # defaulted
        "start_time": request.GET.get("start_time", ""),
        "end_time": request.GET.get("end_time", ""),
        "size": request.GET.get("size", ""),
        "room_category": request.GET.get("room_category", ""),
        "size_options": size_options,
        "room_category_options": room_category_options,
        "results": results,
    })

@login_required
def booking_room_create(request, room_id):
    room = get_object_or_404(Room, pk=room_id)

    # Prefill from query params
    initial = {
        "date": request.GET.get("date") or None,
        "start_time": request.GET.get("start_time") or None,
        "end_time": request.GET.get("end_time") or None,
        "title": request.GET.get("title") or "",
    }
    if request.method == "POST":
        form = BookingCreateForm(request.POST, room=room)
        if form.is_valid():
            try:
                form.save(user=request.user)
                messages.success(request, "Room booked successfully.")
                return redirect("booking_rooms")
            except Exception as exc:
                messages.error(request, str(exc))
    else:
        form = BookingCreateForm(initial=initial, room=room)

    return render(request, "booking/room_book.html", {"active": "res", "category": "rooms", "room": room, "form": form})
