from django import forms
from django.contrib.auth import get_user_model
from .models import Department
from core.models import Role  

#Why use forms in Django?
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
        self.fields["managers"].queryset = User.objects.filter(
            role__in=[Role.MANAGER, Role.GM]
        ).order_by("username")

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
        self.fields["members"].queryset = User.objects.all().order_by("username")
