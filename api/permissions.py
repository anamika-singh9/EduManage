from rest_framework.permissions import BasePermission, SAFE_METHODS


def in_group(user, *names):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=names).exists())


class AdminWriteAuthenticatedRead(BasePermission):
    """Any logged-in user may read; only Admins may write."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return in_group(request.user, 'Admin')


class AdminOrTeacherWrite(BasePermission):
    """Any logged-in user may read (queryset is role-scoped); Admin/Teacher may write."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return in_group(request.user, 'Admin', 'Teacher')
