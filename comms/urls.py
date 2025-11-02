from django.urls import path
from . import views

urlpatterns = [
    path("", views.announcement_list, name="announcement_list"),
    path("new/", views.announcement_create, name="announcement_create"),
    path("<slug:slug>/", views.announcement_detail, name="announcement_detail"),
    path("<slug:slug>/read/", views.announcement_mark_read, name="announcement_mark_read"),
]
