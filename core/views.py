from django.contrib import messages
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
    PasswordChangeView, PasswordChangeDoneView
)
from django.urls import reverse_lazy
from django.conf import settings

class CoreLoginView(LoginView):
    template_name = "auth/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # Matches {% url 'dashboard' %} used in templates
        return reverse_lazy("dashboard")

    def form_valid(self, form):
        messages.success(self.request, "Logged in successfully.")
        return super().form_valid(form)


class CoreLogoutView(LogoutView):
    next_page = "core:login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been logged out.")
        return super().dispatch(request, *args, **kwargs)


class CorePasswordResetView(PasswordResetView):
    template_name = "auth/password_reset_form.html"
    email_template_name = "auth/password_reset_email.html"
    subject_template_name = "auth/password_reset_subject.txt"
    from_email = settings.DEFAULT_FROM_EMAIL
    success_url = reverse_lazy("core:password_reset_done")
    def form_valid(self, form):
        messages.info(self.request, "If an account exists for that email, we’ve sent reset instructions.")
        return super().form_valid(form)

class CorePasswordResetDoneView(PasswordResetDoneView):
    template_name = "auth/password_reset_done.html"


class CorePasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "auth/password_reset_confirm.html"
    success_url = reverse_lazy("core:password_reset_complete")
    post_reset_login = False
    post_reset_login_backend = "django.contrib.auth.backends.ModelBackend"


class CorePasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "auth/password_reset_complete.html"


class CorePasswordChangeView(PasswordChangeView):
    template_name = "auth/password_change_form.html"
    success_url = reverse_lazy("core:password_change_done")

    def form_valid(self, form):
        messages.success(self.request, "Your password was changed.")
        return super().form_valid(form)


class CorePasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "auth/password_change_done.html"