from django.contrib import admin
from .models import Department

# Register your models here.
# Register your models here.
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name","managers_count","members_count")
    search_fields = ("name",)
    filter_horizontal = ("managers","members")
