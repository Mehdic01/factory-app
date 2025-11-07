from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Login/Logout
    path("login/", views.CoreLoginView.as_view(), name="login"),
    path("logout/", views.CoreLogoutView.as_view(), name="logout"),

    # Password reset (forgot password)
    path("password-reset/", views.CorePasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.CorePasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/confirm/<uidb64>/<token>/", views.CorePasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", views.CorePasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # Password change (logged-in users)
    path("password-change/", views.CorePasswordChangeView.as_view(), name="password_change"),
    path("password-change/done/", views.CorePasswordChangeDoneView.as_view(), name="password_change_done"),
]