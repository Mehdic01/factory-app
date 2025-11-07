from django.urls import path
from . import views

urlpatterns = [
    path("", views.announcement_list, name="announcement_list"),
    path("new/", views.announcement_create, name="announcement_create"),
    path("edit/<slug:slug>/", views.announcement_edit, name="announcement_edit"),
    path("<slug:slug>/", views.announcement_detail, name="announcement_detail"),
    path("<slug:slug>/read/", views.announcement_mark_read, name="announcement_mark_read"),
    path("<slug:slug>/archive/", views.announcement_archive, name="announcement_archive"),
    path("<slug:slug>/publish/", views.announcement_publish, name="announcement_publish"),
]
