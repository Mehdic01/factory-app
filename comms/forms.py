from django import forms
from django.utils.text import slugify

from .models import Announcement, AnnouncementStatus
from core.models import Role
from departments.models import Department


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            "title",
            "content",
            "departments",
            "pinned",
            "publish_at",
            "expire_at",
            "status",
            "author",
        ]
        widgets = {
            "publish_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expire_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        # For managers, limit department choices to those they manage
        if user and getattr(user, "role", None) == Role.MANAGER:
            self.fields["departments"].queryset = user.managed_departments.all()
        else:
            # GM/Admin/others see all departments explicitly
            self.fields["departments"].queryset = Department.objects.all()

    def clean(self):
        cleaned = super().clean()
        title = cleaned.get("title")
        if not title:
            return cleaned
        # Pre-generate a unique slug based on title if slug not provided via admin (our form hides slug)
        base = slugify(title)
        if not base:
            return cleaned
        slug = base
        qs = Announcement.objects.all()
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        i = 2
        while qs.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        self._generated_slug = slug
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Only set slug if empty (admin prepopulates otherwise)
        if not obj.slug:
            obj.slug = getattr(self, "_generated_slug", slugify(obj.title or ""))
        if commit:
            obj.save()
            self.save_m2m()
        return obj
