from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages

from .models import Department
from .forms import DepartmentForm, DepartmentManagersForm, DepartmentMembersForm
from core.models import Role
from core.decorators import role_required
from django.contrib.auth import get_user_model
from django.db import transaction


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
@role_required(Role.GM)
def department_create(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created.")
            if request.headers.get("HX-Request"):
                html = render_to_string("departments/_department_form.html", {"form": DepartmentForm()}, request=request)
                return HttpResponse(html)
            return redirect("department_list")
    else:
        form = DepartmentForm()
    tpl = "departments/_department_form.html" if request.headers.get("HX-Request") else "departments/department_form.html"
    return render(request, tpl, {"form": form, "active": "core"})



# Edit a department (only GM can edit and managaers can edit their managed departments)
@role_required(Role.MANAGER, Role.GM)
def department_edit(request, pk):
    dep = get_object_or_404(Department, pk=pk)

    # Manager ise sadece yönettiği departmanı düzenleyebilir
    if request.user.role == Role.MANAGER and (request.user not in dep.managers.all()):
        return HttpResponse(status=403)

    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=dep)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated.")
            if request.headers.get("HX-Request"):
                html = render_to_string("departments/_department_form.html", {"form": form, "dep": dep}, request=request)
                return HttpResponse(html)
            return redirect("department_list")
    else:
        form = DepartmentForm(instance=dep)

    tpl = "departments/_department_form.html" if request.headers.get("HX-Request") else "departments/department_form.html"
    return render(request, tpl, {"form": form, "dep": dep, "active": "core"})


# Assign managers to a department (only GM can assign)
@role_required(Role.GM)
def department_managers(request, pk):
    dep = get_object_or_404(Department, pk=pk)

    User = get_user_model()
    
    def _parse_ids(val: str):
        if not val:
            return set()
        return set(int(x) for x in val.split(',') if x.strip().isdigit())

    def build_context(pending_add=None, pending_remove=None):
        pending_add = pending_add or set()
        pending_remove = pending_remove or set()

        base_current_ids = set(dep.managers.values_list("id", flat=True))
        # Effective current = base ∪ add − remove
        effective_current_ids = (base_current_ids | pending_add) - pending_remove

        # Available = all managers − effective_current
        all_mgr_ids = set(User.objects.filter(role=Role.MANAGER).values_list("id", flat=True))
        effective_available_ids = all_mgr_ids - effective_current_ids

        current_managers = User.objects.filter(id__in=effective_current_ids).order_by("username")
        available_managers = User.objects.filter(id__in=effective_available_ids).order_by("username")
        return {
            "dep": dep,
            "current_managers": current_managers,
            "available_managers": available_managers,
            "pending_add": sorted(list(pending_add)),
            "pending_remove": sorted(list(pending_remove)),
            "active": "core",
        }

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        pending_add = _parse_ids(request.POST.get("pending_add"))
        pending_remove = _parse_ids(request.POST.get("pending_remove"))

        if action in {"add", "remove"} and user_id:
            try:
                manager = User.objects.get(pk=user_id, role=Role.MANAGER)
            except User.DoesNotExist:
                return HttpResponse(status=404)

            uid = manager.id
            base_current_ids = set(dep.managers.values_list("id", flat=True))

            if action == "add":
                # If already scheduled for removal, cancel that; else schedule add
                if uid in pending_remove:
                    pending_remove.discard(uid)
                elif uid not in base_current_ids:
                    pending_add.add(uid)
            elif action == "remove":
                # If scheduled for add, cancel; else schedule removal if currently in base
                if uid in pending_add:
                    pending_add.discard(uid)
                elif uid in base_current_ids:
                    pending_remove.add(uid)

            if request.headers.get("HX-Request"):
                html = render_to_string("departments/_department_managers_form.html", build_context(pending_add, pending_remove), request=request)
                return HttpResponse(html)
            # Non-HTMX: re-render same page with staged changes
            tpl = "departments/department_managers_form.html"
            return render(request, tpl, build_context(pending_add, pending_remove))

        if action == "save":
            # Apply staged changes
            for uid in pending_add:
                dep.managers.add(uid)
            for uid in pending_remove:
                dep.managers.remove(uid)
            messages.success(request, "Managers updated.")
            if request.headers.get("HX-Request"):
                html = render_to_string("departments/_department_managers_form.html", build_context(set(), set()), request=request)
                return HttpResponse(html)
            return redirect("department_managers", pk=dep.pk)

        # Default POST: just re-render with current staged state
        if request.headers.get("HX-Request"):
            html = render_to_string("departments/_department_managers_form.html", build_context(pending_add, pending_remove), request=request)
            return HttpResponse(html)
        return redirect("department_list")

    tpl = "departments/_department_managers_form.html" if request.headers.get("HX-Request") else "departments/department_managers_form.html"
    return render(request, tpl, build_context(set(), set()))


# Assign members to a department (GM can assign to any department, manager can assign to their managed departments)
@role_required(Role.MANAGER, Role.GM)
def department_members(request, pk):
    dep = get_object_or_404(Department, pk=pk)

    if request.user.role == Role.MANAGER and (request.user not in dep.managers.all()):
        return HttpResponse(status=403)

    User = get_user_model()

    # Helper to build context lists
    def _parse_ids(val: str):
        if not val:
            return set()
        return set(int(x) for x in val.split(',') if x.strip().isdigit())

    def build_context(pending_add=None, pending_remove=None):
        pending_add = pending_add or set()
        pending_remove = pending_remove or set()

        base_current_ids = set(dep.members.values_list("id", flat=True))
        effective_current_ids = (base_current_ids | pending_add) - pending_remove

        # Available for members = employees with no department OR those pending removal from this dep, minus those pending add
        unassigned_ids = set(User.objects.filter(role=Role.EMPLOYEE, department__isnull=True).values_list("id", flat=True))
        effective_available_ids = (unassigned_ids | (base_current_ids & pending_remove)) - pending_add

        current_members = User.objects.filter(id__in=effective_current_ids).order_by("username")
        available_members = User.objects.filter(id__in=effective_available_ids).order_by("username")
        return {
            "dep": dep,
            "current_members": current_members,
            "available_members": available_members,
            "pending_add": sorted(list(pending_add)),
            "pending_remove": sorted(list(pending_remove)),
            "active": "core",
        }

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        pending_add = _parse_ids(request.POST.get("pending_add"))
        pending_remove = _parse_ids(request.POST.get("pending_remove"))

        if action in {"add", "remove"} and user_id:
            try:
                member = User.objects.get(pk=user_id, role=Role.EMPLOYEE)
            except User.DoesNotExist:
                return HttpResponse(status=404)

            uid = member.id
            base_current_ids = set(dep.members.values_list("id", flat=True))

            if action == "add":
                # Only allow staging add if user is unassigned or was staged for removal from this dep
                if getattr(member, "department_id", None) and member.department_id != dep.pk and uid not in pending_remove:
                    messages.error(request, f"{member} already belongs to another department.")
                else:
                    if uid in pending_remove:
                        pending_remove.discard(uid)
                    elif uid not in base_current_ids:
                        pending_add.add(uid)
            elif action == "remove":
                if uid in pending_add:
                    pending_add.discard(uid)
                elif uid in base_current_ids:
                    pending_remove.add(uid)

            if request.headers.get("HX-Request"):
                html = render_to_string("departments/_department_members_form.html", build_context(pending_add, pending_remove), request=request)
                return HttpResponse(html)
            # Non-HTMX: re-render same page with staged changes
            tpl = "departments/department_members_form.html"
            return render(request, tpl, build_context(pending_add, pending_remove))

        if action == "save":
            # Apply staged changes
            with transaction.atomic():
                # Adds
                for uid in pending_add:
                    m = User.objects.filter(pk=uid, role=Role.EMPLOYEE).first()
                    if not m:
                        continue
                    # Enforce single department
                    if getattr(m, "department_id", None) and m.department_id not in (None, dep.pk):
                        # Skip if somehow became assigned elsewhere during staging
                        continue
                    m.department = dep
                    m.save(update_fields=["department"])
                    dep.members.add(m)
                # Removes
                for uid in pending_remove:
                    m = User.objects.filter(pk=uid, role=Role.EMPLOYEE).first()
                    if not m:
                        continue
                    dep.members.remove(m)
                    if getattr(m, "department_id", None) == dep.pk:
                        m.department = None
                        m.save(update_fields=["department"])
            messages.success(request, "Members updated.")
            if request.headers.get("HX-Request"):
                html = render_to_string("departments/_department_members_form.html", build_context(set(), set()), request=request)
                return HttpResponse(html)
            return redirect("department_members", pk=dep.pk)

        # Default POST: re-render with staged state
        if request.headers.get("HX-Request"):
            html = render_to_string("departments/_department_members_form.html", build_context(pending_add, pending_remove), request=request)
            return HttpResponse(html)
        return redirect("department_list")

    tpl = "departments/_department_members_form.html" if request.headers.get("HX-Request") else "departments/department_members_form.html"
    return render(request, tpl, build_context(set(), set()))

