from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages

from .models import Department
from .forms import DepartmentForm, DepartmentManagersForm, DepartmentMembersForm
from core.models import Role
from core.decorators import role_required


# List all departments (based on user role--> if manager, show only managed departments and if gm show all departments)

@role_required(Role.MANAGER, Role.GM)
def department_list(request):
    u = request.user
    if u.role == Role.MANAGER:
        qs = Department.objects.filter(managers=u)
    else:
        qs = Department.objects.all()
    return render(request, "departments/department_list.html", {"departments": qs, "active": "core"})


# Create a new department (only GM can create)
