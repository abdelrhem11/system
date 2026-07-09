from apps.users.models import AuditLog


def request_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")


def log_audit(*, request, action, instance, metadata=None):
    user = request.user if request and request.user.is_authenticated else None
    AuditLog.objects.create(user=user, action=action, entity_type=instance.__class__.__name__, entity_id=instance.id, metadata=metadata or {}, ip_address=request_ip(request) if request else None)
