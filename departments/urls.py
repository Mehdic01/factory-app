from django.urls import path
from . import views

urlpatterns = [
    path("departments/", views.department_list, name="department_list"),
    path("departments/create/", views.department_create, name="department_create"),
    path("departments/<int:pk>/edit/", views.department_edit, name="department_edit"),
    path("departments/<int:pk>/managers/", views.department_managers, name="department_managers"),
    path("departments/<int:pk>/members/", views.department_members, name="department_members"),
]
