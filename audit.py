import json

from .models import AuditLog


def client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
    return ip or None


def _s(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def log(request, action, inspection=None, field_key="", old=None, new=None, details="", user=None):
    AuditLog.objects.create(
        user=user if user is not None else (request.user if request and request.user.is_authenticated else None),
        inspection=inspection,
        action=action,
        field_key=field_key,
        old_value=_s(old)[:5000],
        new_value=_s(new)[:5000],
        details=details[:2000],
        ip=client_ip(request),
    )
