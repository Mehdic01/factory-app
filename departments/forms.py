from django import forms
from django.contrib.auth import get_user_model
from .models import Department
from core.models import Role  

# Why use forms in Django?
#Validation: Forms automatically check if the data entered by the user is valid (e.g., required fields, correct types).
#Security: Forms help prevent security issues like SQL injection and CSRF attacks.
#Convenience: Forms can be tied to models (ModelForm), making it easy to create or update database records.
#Rendering: Forms can generate HTML form elements for you.

User = get_user_model()


# Form for creating/editing a department
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("name",)

# Form for assigning managers to a department
class DepartmentManagersForm(forms.ModelForm):
    managers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 10}),
        label="Managers",
    )
    class Meta:
        model = Department
        fields = ("managers",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Base queryset: users who can be department managers
        base_qs = User.objects.filter(
            role__in=[Role.MANAGER, Role.GM]
        ).order_by("username")
        self.fields["managers"].queryset = base_qs

        # Group into current vs available for nicer UI
        current_qs = User.objects.none()
        if getattr(self.instance, "pk", None):
            current_qs = self.instance.managers.all().order_by("username")
        current_ids = list(current_qs.values_list("id", flat=True))
        available_qs = base_qs.exclude(id__in=current_ids)

        def _label(u):
            full = getattr(u, "get_full_name", None)
            try:
                name = full() if callable(full) else None
            except Exception:
                name = None
            return name or getattr(u, "username", str(u.pk))

        grouped_choices = [
            ("Department's current managers", [(u.id, _label(u)) for u in current_qs]),
            ("Available managers", [(u.id, _label(u)) for u in available_qs]),
        ]
        self.fields["managers"].choices = grouped_choices

# Form for assigning members to a department
class DepartmentMembersForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 14}),
        label="Members",
    )
    class Meta:
        model = Department
        fields = ("members",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Base queryset: employees for membership
        base_qs = User.objects.filter(role=Role.EMPLOYEE).order_by("username")
        self.fields["members"].queryset = base_qs

        # Group into current vs available for nicer UI
        current_qs = User.objects.none()
        if getattr(self.instance, "pk", None):
            current_qs = self.instance.members.all().order_by("username")
        current_ids = list(current_qs.values_list("id", flat=True))
        available_qs = base_qs.exclude(id__in=current_ids)

        def _label(u):
            full = getattr(u, "get_full_name", None)
            try:
                name = full() if callable(full) else None
            except Exception:
                name = None
            return name or getattr(u, "username", str(u.pk))

        grouped_choices = [
            ("Department's current members", [(u.id, _label(u)) for u in current_qs]),
            ("Available members", [(u.id, _label(u)) for u in available_qs]),
        ]
        self.fields["members"].choices = grouped_choices
