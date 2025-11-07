# booking/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def task_list(request):
    return render(request, "tasks/list.html", {"active": "tasks"})

@login_required
def announcement_list(request):
    return render(request, "announcements/list.html", {"active": "announcements"})

@login_required
def booking_list(request):
    category = request.GET.get("type", "rooms")  # 'rooms' or 'cars'
    date = request.GET.get("date")
    start_time = request.GET.get("start_time")
    end_time = request.GET.get("end_time")
    size = request.GET.get("size")
    purpose = request.GET.get("purpose")

    if category == "cars":
        size_options = [("2", "2 seats"), ("5", "5 seats"), ("7", "7+ seats")]
        purpose_options = [
            ("client_visit", "Client visit"),
            ("delivery", "Delivery"),
            ("commute", "Commute"),
            ("airport", "Airport pickup"),
            ("other", "Other"),
        ]
    else:
        category = "rooms"
        size_options = [("small", "Small (1–4)"), ("medium", "Medium (4–8)"), ("large", "Large (8+)")]
        purpose_options = [
            ("meeting", "Meeting"),
            ("training", "Training"),
            ("interview", "Interview"),
            ("client_call", "Client call"),
            ("other", "Other"),
        ]

    results = []  # TODO: replace with real availability
    return render(request, "booking/booking_list.html", {
        "active": "res",
        "category": category,
        "date": date or "",
        "start_time": start_time or "",
        "end_time": end_time or "",
        "size": size or "",
        "purpose": purpose or "",
        "size_options": size_options,
        "purpose_options": purpose_options,
        "results": results,
    })

@login_required
def feedback_list(request):
    return render(request, "feedback/list.html", {"active": "feedback"})
