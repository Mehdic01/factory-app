from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def role_required(*allowed_roles):
    def outer(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped
    return outer
