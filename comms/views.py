from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db.models import Prefetch, Q
from django.core.exceptions import ValidationError

from .models import Announcement, AnnouncementRead, AnnouncementStatus
from .forms import AnnouncementForm
from core.models import Role


def _user_department_ids(user):
    """Collect all department IDs relevant to the user (member, manager, and FK)."""
    ids = set()
    # From M2M relationships via Department.related_name
    if hasattr(user, "member_departments"):
        ids.update(user.member_departments.values_list("id", flat=True))
    if hasattr(user, "managed_departments"):
        ids.update(user.managed_departments.values_list("id", flat=True))
    # From User.department FK
    if getattr(user, "department_id", None):
        ids.add(user.department_id)
    return list(ids)


# Create your views here.
@login_required
def announcement_list(request):
    dept_ids = _user_department_ids(request.user)
    # Manager-specific split view: "My Announcements" (no read button) and "GM Announcements" (with read button)
    if getattr(request.user, "role", None) == Role.MANAGER:
        # Filter selector for "My Announcements": ALL (default), DRAFTS, ARCHIVED
        filter_opt = (request.GET.get("f") or "ALL").upper()
        if filter_opt not in ("ALL", "DRAFTS", "ARCHIVED"):
            filter_opt = "ALL"

        base_my = Announcement.objects.filter(author=request.user).select_related("author").prefetch_related("departments")
        if filter_opt == "DRAFTS":
            my_qs = base_my.filter(status=AnnouncementStatus.DRAFT)
        elif filter_opt == "ARCHIVED":
            my_qs = base_my.filter(status=AnnouncementStatus.ARCHIVED)
        else:  # ALL => exclude archived
            my_qs = base_my.exclude(status=AnnouncementStatus.ARCHIVED)

        my_qs = my_qs.order_by("-pinned", "-publish_at", "-created_at")
        gm_qs = (
            Announcement.objects.active()
            .for_departments(dept_ids)
            .filter(author__role=Role.GM)
            .select_related("author")
            .prefetch_related("departments")
        )

        read_ids = set(
            AnnouncementRead.objects.filter(user=request.user, announcement__in=gm_qs)
            .values_list("announcement_id", flat=True)
        )

        context = {
            "active": "comms",
            "is_manager": True,
            "my_announcements": my_qs,
            "gm_announcements": gm_qs,
            "read_ids": read_ids,
            "current_filter": filter_opt,
        }
        return render(request, "comms/announcement_list.html", context)

    # GM-specific: show "My Announcements" and "All Announcements" (excluding own), with read button only on the latter
    if getattr(request.user, "role", None) == Role.GM:
        # GM: filter selector for "My Announcements": ALL (default), DRAFTS, ARCHIVED
        filter_opt = (request.GET.get("f") or "ALL").upper()
        if filter_opt not in ("ALL", "DRAFTS", "ARCHIVED"):
            filter_opt = "ALL"

        base_my = Announcement.objects.filter(author=request.user).select_related("author").prefetch_related("departments")
        if filter_opt == "DRAFTS":
            my_qs = base_my.filter(status=AnnouncementStatus.DRAFT)
        elif filter_opt == "ARCHIVED":
            my_qs = base_my.filter(status=AnnouncementStatus.ARCHIVED)
        else:  # ALL => exclude archived
            my_qs = base_my.exclude(status=AnnouncementStatus.ARCHIVED)

        my_qs = my_qs.order_by("-pinned", "-publish_at", "-created_at")
        all_qs = (
            Announcement.objects.active()
            .exclude(author=request.user)
            .select_related("author")
            .prefetch_related("departments")
        )

        read_ids = set(
            AnnouncementRead.objects.filter(user=request.user, announcement__in=all_qs)
            .values_list("announcement_id", flat=True)
        )

        context = {
            "active": "comms",
            "is_gm": True,
            "my_announcements": my_qs,
            "all_announcements": all_qs,
            "read_ids": read_ids,
            "current_filter": filter_opt,
        }
        return render(request, "comms/announcement_list.html", context)

    # Default behavior for GM and EMPLOYEE: single list with read button
    qs = (
        Announcement.objects.published()
        .active()
        .for_departments(dept_ids)
        .select_related("author")
        .prefetch_related("departments")
    )

    page_number = request.GET.get("page", 1)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)

    read_ids = set(
        AnnouncementRead.objects.filter(user=request.user, announcement__in=page_obj.object_list)
        .values_list("announcement_id", flat=True)
    )

    context = {
        "active": "comms",
        "page_obj": page_obj,
        "read_ids": read_ids,
    }
    return render(request, "comms/announcement_list.html", context)


@login_required
def announcement_detail(request, slug: str):
    user = request.user
    dept_ids = _user_department_ids(user)

    base = Announcement.objects.select_related("author").prefetch_related("departments")
    active_qs = base.active().for_departments(dept_ids)

    # First, try to fetch as an active, visible announcement
    try:
        announcement = active_qs.get(slug=slug)
        is_read = announcement.is_read_by(user)
    except Announcement.DoesNotExist:
        # Fallback rules:
        # - GM can view any announcement by slug (even drafts/scheduled)
        # - Manager can view their own announcements (any status)
        if getattr(user, "role", None) == Role.GM:
            announcement = get_object_or_404(base, slug=slug)
            is_read = announcement.is_live and announcement.is_read_by(user)
        elif getattr(user, "role", None) == Role.MANAGER:
            announcement = get_object_or_404(
                base.filter(Q(author=user)),
                slug=slug,
            )
            is_read = announcement.is_live and announcement.is_read_by(user)
        else:
            # Employees should not see non-active/non-visible announcements
            return render(request, "404.html", status=404)
    return render(request, "comms/announcement_detail.html", {
        "active": "comms",
        "announcement": announcement,
        "is_read": is_read,
    })


@login_required
def announcement_edit(request, slug: str):
    # Permissions: GM can edit any; Manager can edit only own
    ann = get_object_or_404(Announcement, slug=slug)
    if getattr(request.user, "role", None) == Role.MANAGER and ann.author_id != request.user.id:
        return HttpResponseForbidden("You do not have permission to edit this announcement.")
    if getattr(request.user, "role", None) not in (Role.GM, Role.MANAGER):
        return HttpResponseForbidden("You do not have permission to edit announcements.")

    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=ann, user=request.user)
        if form.is_valid():
            ann = form.save(commit=False)
            # Preserve author; ensure it exists
            if not ann.author_id:
                ann.author = request.user
            ann.save()
            form.save_m2m()

            desired_status = form.cleaned_data.get("status")
            try:
                if desired_status == AnnouncementStatus.PUBLISHED:
                    ann.publish()
                elif desired_status == AnnouncementStatus.ARCHIVED:
                    ann.archive()
            except ValidationError as e:
                form.add_error(None, e)
                return render(request, "comms/announcement_form.html", {"form": form, "active": "comms", "is_create": False})

            return redirect("announcement_detail", slug=ann.slug)
    else:
        form = AnnouncementForm(instance=ann, user=request.user)

    return render(request, "comms/announcement_form.html", {"form": form, "active": "comms", "is_create": False})


@login_required
@require_POST
def announcement_archive(request, slug: str):
    ann = get_object_or_404(Announcement, slug=slug)
    # Only author or GM can archive
    if getattr(request.user, "role", None) == Role.MANAGER and ann.author_id != request.user.id:
        return HttpResponseForbidden("You do not have permission to archive this announcement.")
    if getattr(request.user, "role", None) not in (Role.GM, Role.MANAGER):
        return HttpResponseForbidden("You do not have permission to archive announcements.")
    ann.archive()
    return redirect("announcement_list")


@login_required
@require_POST
def announcement_publish(request, slug: str):
    ann = get_object_or_404(Announcement, slug=slug)
    # Only author or GM can publish; validations inside publish()
    if getattr(request.user, "role", None) == Role.MANAGER and ann.author_id != request.user.id:
        return HttpResponseForbidden("You do not have permission to publish this announcement.")
    if getattr(request.user, "role", None) not in (Role.GM, Role.MANAGER):
        return HttpResponseForbidden("You do not have permission to publish announcements.")
    ann.author = ann.author or request.user
    try:
        ann.publish()
    except ValidationError as e:
        # On failure, send user to edit form with error
        form = AnnouncementForm(instance=ann, user=request.user)
        form.add_error(None, e)
        return render(request, "comms/announcement_form.html", {"form": form, "active": "comms", "is_create": False})
    return redirect("announcement_detail", slug=ann.slug)


@login_required
@require_POST
def announcement_mark_read(request, slug: str):
    dept_ids = _user_department_ids(request.user)
    announcement = get_object_or_404(
        Announcement.objects.active().for_departments(dept_ids), slug=slug
    )
    announcement.mark_read(request.user)

    # HTMX support: return just the button fragment
    if request.headers.get("HX-Request") == "true":
        return render(request, "comms/_read_button.html", {"announcement": announcement, "is_read": True})

    # Fallback
    return render(request, "comms/announcement_detail.html", {
        "active": "comms",
        "announcement": announcement,
        "is_read": True,
    })


@login_required
def announcement_create(request):
    # Permissions: only GM or MANAGER can create/publish (employees cannot)
    if getattr(request.user, "role", None) not in (Role.GM, Role.MANAGER):
        return HttpResponseForbidden("You do not have permission to create announcements.")

    if request.method == "POST":
        form = AnnouncementForm(request.POST, user=request.user)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.author = request.user
            ann.save()
            form.save_m2m()

            desired_status = form.cleaned_data.get("status")
            try:
                if desired_status == AnnouncementStatus.PUBLISHED:
                    ann.publish()
                elif desired_status == AnnouncementStatus.ARCHIVED:
                    ann.archive()
            except ValidationError as e:
                # Roll back to draft state and show errors
                ann.status = AnnouncementStatus.DRAFT
                ann.save(update_fields=["status"])
                form.add_error(None, e)
                return render(request, "comms/announcement_form.html", {"form": form, "active": "comms", "is_create": True})

            return redirect("announcement_detail", slug=ann.slug)
    else:
        form = AnnouncementForm(user=request.user)

    return render(request, "comms/announcement_form.html", {"form": form, "active": "comms", "is_create": True})
