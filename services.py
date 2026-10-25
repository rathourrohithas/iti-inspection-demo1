"""Business logic shared by views, imports and tests."""
import copy
import datetime

from django.db import transaction
from django.utils import timezone

from . import audit
from .models import Inspection, PortalSettings, TeamMember
from .proforma import PROFORMA_VERSION
from .schema import (input_specs, invalid_values, missing_mandatory, part_of_key, pct, progress,
                     validate_value)


def _full_name(u):
    return u.get_full_name() or u.username


def team_rows(insp):
    rows = []
    for tm in insp.team.select_related("user", "user__profile").order_by("-role", "id"):
        prof = getattr(tm.user, "profile", None)
        rows.append({
            "user_id": tm.user_id,
            "name": _full_name(tm.user),
            "designation": prof.designation if prof else "",
            "office": prof.office if prof else "",
            "role": tm.role,
        })
    return rows


def seed_prefill(insp, refresh_team=False):
    """Pre-fill ITI master details and team details into a not-yet-started form.
    Pre-filled values remain editable by the team."""
    data = dict(insp.data or {})
    iti = insp.iti
    pre = {
        "SA.A1": iti.name, "SA.A2": iti.mis_code, "SA.A3.address": iti.address,
        "SA.A3.block": iti.block, "SA.A3.district": iti.district,
        "SA.A5.name": iti.principal_name, "SA.A5.mobile": iti.principal_mobile,
        "SA.A5.email": iti.principal_email,
    }
    for k, v in pre.items():
        if v and not data.get(k):
            data[k] = v
    team = team_rows(insp)
    if refresh_team or not data.get("SA.A9"):
        data["SA.A9"] = [{"name": t["name"], "designation": t["designation"], "office": t["office"]} for t in team]
    old_members = {m.get("user_id"): m for m in data.get("SA.J8.members") or [] if isinstance(m, dict)}
    if refresh_team or not data.get("SA.J8.members"):
        members = []
        for t in team:
            old = old_members.get(t["user_id"], {})
            members.append({
                "user_id": t["user_id"], "name": t["name"],
                "designation": ", ".join(x for x in (t["designation"], t["office"]) if x),
                "declared": bool(old.get("declared")), "declared_at": old.get("declared_at", ""),
                "declared_by": old.get("declared_by", ""), "date": old.get("date", ""),
            })
        data["SA.J8.members"] = members
    insp.data = data
    insp.progress_pct = progress(data, iti.is_govt)["pct"]
    if not insp.proforma_version:
        insp.proforma_version = PROFORMA_VERSION


def _apply_calcs(key, value):
    """Recompute prescribed calculations (G1 pass %)."""
    if key == "SA.G1" and isinstance(value, list):
        for row in value:
            if isinstance(row, dict):
                for y in ("y1", "y2", "y3"):
                    p = pct(row.get(f"{y}_pass"), row.get(f"{y}_app"))
                    row[f"{y}_pct"] = p if p != "" else None
                    if row[f"{y}_pct"] is None:
                        row.pop(f"{y}_pct")
    return value


def _merge_declarations(old_rows, new_rows, user):
    """Each logged-in member can make or withdraw only their own declaration."""
    old_by_uid = {r.get("user_id"): r for r in (old_rows or []) if isinstance(r, dict) and r.get("user_id")}
    out = []
    for row in new_rows or []:
        if not isinstance(row, dict):
            continue
        row = dict(row)
        uid = row.get("user_id")
        old = old_by_uid.get(uid, {})
        if uid and uid == user.id:
            if row.get("declared") and not old.get("declared"):
                row["declared_at"] = timezone.localtime().strftime("%d-%m-%Y %H:%M")
                row["declared_by"] = _full_name(user)
            elif not row.get("declared"):
                row["declared"] = False
                row["declared_at"] = ""
                row["declared_by"] = ""
            else:
                row["declared_at"] = old.get("declared_at", "")
                row["declared_by"] = old.get("declared_by", "")
        elif uid:
            # Someone else's row: their name and declaration are protected.
            row["name"] = old.get("name", row.get("name", ""))
            row["declared"] = bool(old.get("declared"))
            row["declared_at"] = old.get("declared_at", "")
            row["declared_by"] = old.get("declared_by", "")
        else:
            # Rows typed in manually (no portal login) cannot be signed electronically.
            row["declared"] = False
            row["declared_at"] = ""
            row["declared_by"] = ""
        out.append(row)
    # A member cannot remove another member's signed declaration.
    present = {r.get("user_id") for r in out}
    for uid, old in old_by_uid.items():
        if uid != user.id and old.get("declared") and uid not in present:
            out.append(dict(old))
    return out


class SaveResult:
    def __init__(self):
        self.saved = []
        self.errors = {}
        self.insp = None


def save_changes(request, insp_id, changes, editable):
    """Apply a dict of {input_key: value} to an inspection. Returns SaveResult."""
    res = SaveResult()
    specs = input_specs()
    with transaction.atomic():
        insp = Inspection.objects.select_for_update().select_related("iti").get(pk=insp_id)
        res.insp = insp
        if insp.is_locked:
            res.errors["_form"] = "This inspection has been submitted and is locked."
            return res
        data = copy.deepcopy(insp.data or {})
        logs = []
        for key, value in changes.items():
            if key not in specs:
                res.errors[key] = "Unknown field."
                continue
            part = part_of_key(key)
            if part not in editable:
                res.errors[key] = "You are not authorised to edit this section."
                continue
            if isinstance(value, str):
                value = value.strip() if specs[key]["t"] not in ("textarea",) else value
            err = validate_value(key, value)
            if err:
                res.errors[key] = f"Value {err}."
                continue
            if specs[key]["t"] == "members":
                value = _merge_declarations(data.get(key), value, request.user)
            value = _apply_calcs(key, value)
            old = data.get(key)
            if value in ("", None, []):
                if key in data:
                    data.pop(key)
                    logs.append((key, old, None))
            elif old != value:
                data[key] = value
                logs.append((key, old, value))
            res.saved.append(key)
        if logs:
            insp.data = data
            insp.version += 1
            insp.progress_pct = progress(data, insp.iti.is_govt)["pct"]
            if insp.status == Inspection.NOT_STARTED:
                insp.status = Inspection.IN_PROGRESS
                insp.started_at = timezone.now()
                audit.log(request, "STARTED", insp)
            insp.save()
            for key, old, new in logs:
                audit.log(request, "FIELD_CHANGED", insp, key, old, new)
    return res


def submission_blockers(insp):
    """Reasons the form cannot be submitted (configured mandatory items, invalid values)."""
    settings_obj = PortalSettings.get()
    data = insp.data or {}
    missing = missing_mandatory(data, settings_obj.mandatory_units, insp.iti.is_govt)
    invalid = invalid_values(data)
    return missing, invalid


def submit(request, insp_id):
    """Returns (ok: bool, message: str)."""
    with transaction.atomic():
        insp = Inspection.objects.select_for_update().select_related("iti").get(pk=insp_id)
        if insp.status == Inspection.SUBMITTED:
            return False, "This inspection was already submitted on %s." % timezone.localtime(insp.submitted_at).strftime("%d-%m-%Y %H:%M")
        missing, invalid = submission_blockers(insp)
        if missing or invalid:
            return False, "Please complete the mandatory items and correct invalid entries before submitting."
        insp.status = Inspection.SUBMITTED
        insp.submitted_at = timezone.now()
        insp.submitted_by = request.user
        insp.return_reason = ""
        insp.save()
        audit.log(request, "SUBMITTED", insp, details=f"version {insp.version}, progress {insp.progress_pct}%")
    return True, "Inspection submitted. The form is now locked."


def return_for_correction(request, insp_id, reason):
    with transaction.atomic():
        insp = Inspection.objects.select_for_update().get(pk=insp_id)
        if insp.status != Inspection.SUBMITTED:
            return False, "Only submitted inspections can be returned."
        insp.status = Inspection.RETURNED
        insp.return_reason = reason
        insp.save()
        audit.log(request, "RETURNED", insp, details=reason)
    return True, "Returned to the team for correction."


def parse_date(v):
    if isinstance(v, datetime.date):
        return v
    v = str(v or "").strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.datetime.strptime(v, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date: {v!r}")
