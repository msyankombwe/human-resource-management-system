from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    """Restrict a view to users whose profile role is in the given roles."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)
            if profile is None or profile.role not in roles:
                messages.error(request, 'You do not have permission to access that page.')
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def hr_required(view_func):
    return role_required('ADMIN', 'HR')(view_func)


def manager_required(view_func):
    return role_required('ADMIN', 'HR', 'MANAGER')(view_func)


def admin_required(view_func):
    return role_required('ADMIN')(view_func)
