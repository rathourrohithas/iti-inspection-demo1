"""Role and object-level access rules."""
from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import Inspection, Profile, TeamMember


def role_of(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return Profile.ADMIN
    prof = getattr(user, "profile", None)
    return prof.role if prof else Profile.INSPECTOR


def is_admin(user):
    return role_of(user) == Profile.ADMIN


def is_directorate(user):
    return role_of(user) in (Profile.ADMIN, Profile.VIEWER)


def admin_required(view):
    @wraps(view)
    def wrapper(request, *a, **kw):
        if not is_admin(request.user):
            raise PermissionDenied
        return view(request, *a, **kw)
    return wrapper


def directorate_required(view):
    @wraps(view)
    def wrapper(request, *a, **kw):
        if not is_directorate(request.user):
            raise PermissionDenied
        return view(request, *a, **kw)
    return wrapper


def visible_inspections(user):
    qs = Inspection.objects.select_related("iti")
    if is_directorate(user):
        return qs
    return qs.filter(team__user=user).distinct()


def can_view(user, insp):
    return is_directorate(user) or insp.team.filter(user=user).exists()


def editable_parts(user, insp):
    """Set of part keys the user may edit now, or empty set."""
    from .schema import parts_list
    if insp.is_locked:
        return set()
    tm = insp.team.filter(user=user).first()
    if not tm:
        return set()
    keys = {p["key"] for p in parts_list() if not (p["govt_only"] and not insp.iti.is_govt)}
    if tm.role == TeamMember.LEADER or not tm.sections:
        return keys
    return keys & set(tm.sections)


def is_leader(user, insp):
    return insp.team.filter(user=user, role=TeamMember.LEADER).exists()
