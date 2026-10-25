from django.conf import settings

from .access import role_of


def portal_context(request):
    user = getattr(request, "user", None)
    return {
        "PORTAL_NAME": settings.PORTAL_NAME,
        "PORTAL_DEPARTMENT": settings.PORTAL_DEPARTMENT,
        "user_role": role_of(user) if user and user.is_authenticated else None,
        "DEMO_MODE": getattr(settings, "DEMO_MODE", False),
    }
