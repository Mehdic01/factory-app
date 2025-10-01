from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from core.models import Role

@login_required
def dashboard(request):
    if request.user.role == Role.EMPLOYEE:
        return render(request, "dashboard/employee_dashboard.html", {"active": None})
    return render(request, "dashboard/manager_dashboard.html", {"active": None})
