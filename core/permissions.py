from rest_framework.permissions import BasePermission


class IsAdminOrReceptionist(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role in {"admin", "receptionist"})


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "doctor")
