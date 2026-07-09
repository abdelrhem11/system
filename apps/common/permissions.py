from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    role_map = {
        "view": {"admin", "warehouse_manager", "warehouse_keeper", "accountant", "viewer"},
        "create": {"admin", "warehouse_manager", "warehouse_keeper"},
        "update": {"admin", "warehouse_manager"},
        "delete": {"admin"},
    }

    def has_permission(self, request, view):
        if request.user and request.user.is_superuser:
            return True
        action = getattr(view, "action", "view")
        bucket = "view" if action in {"list", "retrieve"} else "create" if action == "create" else "update" if action in {"update", "partial_update", "approve"} else "delete" if action == "destroy" else "update"
        groups = set(request.user.groups.values_list("name", flat=True)) if request.user and request.user.is_authenticated else set()
        return bool(groups & self.role_map[bucket])
