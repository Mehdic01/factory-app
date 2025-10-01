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
    return render(request, "bookings/list.html", {"active": "bookings"})

@login_required
def feedback_list(request):
    return render(request, "feedback/list.html", {"active": "feedback"})
