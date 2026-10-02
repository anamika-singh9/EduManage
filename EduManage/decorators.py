"""
Role-based access decorators built on Django's real authentication system
(django.contrib.auth.User + Groups), replacing the old pattern of storing a
plain string in the session (session['admin'], session['teacherid'], ...)
and hand-checking it in every view.

Usage:
    @admin_required
    def adminhome(request):
        ...
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def group_required(*group_names):
    """Only allow a logged-in user who belongs to one of `group_names`."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser or request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You don't have permission to view this page.")
        return wrapper
    return decorator


admin_required = group_required('Admin')
teacher_required = group_required('Teacher')
student_required = group_required('Student')
parent_required = group_required('Parent')
