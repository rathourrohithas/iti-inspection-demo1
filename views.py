import json
import mimetypes
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from . import audit, services
from .access import (can_view, editable_parts, is_admin, is_directorate, is_leader, role_of,
                     visible_inspections)
from .models import Attachment, Inspection, PortalSettings, TeamMember
from .proforma import CORRECTIONS, PROFORMA
from .schema import (applicable_units, j2_summary, part_progress, parts_list, progress, unit_answered,
                     units_by_key)


@login_required
def home(request):
    if is_directorate(request.user):
        return redirect("dashboard")
    return redirect("my_inspections")


@login_required
def my_inspections(request):
    qs = (Inspection.objects.filter(team__user=request.user).select_related("iti")
          .prefetch_related("team__user").distinct().order_by("status", "scheduled_date"))
    rows = []
    for insp in qs:
        tm = next((t for t in insp.team.all() if t.user_id == request.user.id), None)
        rows.append({"insp": insp, "tm": tm})
    return render(request, "inspections/my_inspections.html", {"rows": rows, "today": timezone.localdate()})


def _attachments_payload(insp, request):
    out = {}
    for a in insp.attachments.filter(deleted=False).select_related("uploaded_by"):
        out.setdefault(a.unit_key, []).append({
            "id": a.id, "name": a.original_name, "size": a.size, "image": a.is_image,
            "caption": a.caption,
            "url": reverse("attachment_file", args=[a.id]),
            "by": (a.uploaded_by.get_full_name() or a.uploaded_by.username) if a.uploaded_by else "",
            "can_delete": bool(a.uploaded_by_id == request.user.id or is_leader(request.user, insp)),
        })
    return out


def _form_context(request, insp, mode):
    editable = sorted(editable_parts(request.user, insp)) if mode == "edit" else []
    ps = PortalSettings.get()
    ctx = {
        "inspection_id": insp.id,
        "mode": mode,
        "version": insp.version,
        "status": insp.status,
        "editable_parts": editable,
        "is_leader": is_leader(request.user, insp),
        "user_id": request.user.id,
        "iti_is_govt": insp.iti.is_govt,
        "mandatory_units": ps.mandatory_units,
        "upload": {"max_mb": ps.max_upload_mb, "types": ps.allowed_ext_list()},
        "urls": {
            "save": reverse("api_save", args=[insp.id]),
            "upload": reverse("api_upload", args=[insp.id]),
            "delete": reverse("api_delete_attachment", args=[insp.id, 0]).rsplit("/0/", 1)[0] + "/",
            "review": reverse("inspection_review", args=[insp.id]),
        },
        "parts": parts_list(),
    }
    return {
        "insp": insp,
        "schema_json": PROFORMA,
        "data_json": insp.data or {},
        "ctx_json": ctx,
        "att_json": _attachments_payload(insp, request),
        "mode": mode,
        "is_leader": ctx["is_leader"],
    }


@never_cache
@login_required
def inspection_form(request, pk):
    insp = get_object_or_404(Inspection.objects.select_related("iti"), pk=pk)
    if not insp.team.filter(user=request.user).exists():
        if can_view(request.user, insp):
            return redirect("record_view", pk=pk)
        raise PermissionDenied
    if insp.is_locked:
        messages.info(request, "This inspection has been submitted and is locked. Showing the read-only record.")
        return redirect("record_view", pk=pk)
    return render(request, "inspections/form.html", _form_context(request, insp, "edit"))


@login_required
def record_view(request, pk):
    insp = get_object_or_404(Inspection.objects.select_related("iti"), pk=pk)
    if not can_view(request.user, insp):
        raise PermissionDenied
    ctx = _form_context(request, insp, "view")
    ctx["history"] = insp.audit.exclude(action="FIELD_CHANGED").select_related("user")[:50]
    return render(request, "inspections/record.html", ctx)


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return None


@require_POST
@login_required
def api_save(request, pk):
    insp = get_object_or_404(Inspection.objects.select_related("iti"), pk=pk)
    if not insp.team.filter(user=request.user).exists():
        return JsonResponse({"ok": False, "error": "Not authorised."}, status=403)
    body = _json_body(request)
    if body is None or not isinstance(body.get("changes"), dict):
        return JsonResponse({"ok": False, "error": "Invalid request."}, status=400)
    editable = editable_parts(request.user, insp)
    res = services.save_changes(request, insp.id, body["changes"], editable)
    insp = res.insp
    status = 200
    if "_form" in res.errors:
        status = 409
    data = insp.data or {}
    return JsonResponse({
        "ok": not res.errors,
        "saved": res.saved,
        "errors": res.errors,
        "version": insp.version,
        "status": insp.status,
        "progress": progress(data, insp.iti.is_govt),
        "part_progress": part_progress(data, insp.iti.is_govt),
        "j2": j2_summary(data),
        # Server-side values for keys whose value the server may adjust (calculations, declarations).
        "values": {k: data.get(k) for k in res.saved if k in ("SA.G1", "SA.J8.members")},
        "saved_at": timezone.localtime().strftime("%H:%M:%S"),
    }, status=status)


def _sniff_ok(f, ext):
    head = f.read(16)
    f.seek(0)
    if ext == "pdf":
        return head.startswith(b"%PDF-")
    if ext in ("jpg", "jpeg"):
        return head.startswith(b"\xff\xd8\xff")
    if ext == "png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    return True


@require_POST
@login_required
def api_upload(request, pk):
    insp = get_object_or_404(Inspection.objects.select_related("iti"), pk=pk)
    if not insp.team.filter(user=request.user).exists():
        return JsonResponse({"ok": False, "error": "Not authorised."}, status=403)
    if insp.is_locked:
        return JsonResponse({"ok": False, "error": "This inspection is submitted and locked."}, status=409)
    unit_key = request.POST.get("unit_key", "")
    unit = units_by_key().get(unit_key)
    if not unit:
        return JsonResponse({"ok": False, "error": "Unknown item."}, status=400)
    if unit.part_key not in editable_parts(request.user, insp):
        return JsonResponse({"ok": False, "error": "You are not authorised to edit this section."}, status=403)
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"ok": False, "error": "No file received."}, status=400)
    ps = PortalSettings.get()
    ext = os.path.splitext(f.name)[1].lower().lstrip(".")
    if ext not in ps.allowed_ext_list():
        return JsonResponse({"ok": False, "error": f"File type .{ext} is not allowed. Allowed: {', '.join(ps.allowed_ext_list())}."}, status=400)
    if f.size > ps.max_upload_mb * 1024 * 1024:
        return JsonResponse({"ok": False, "error": f"File is larger than {ps.max_upload_mb} MB."}, status=400)
    if not _sniff_ok(f, ext):
        return JsonResponse({"ok": False, "error": "The file content does not match its type."}, status=400)
    ctype = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "pdf": "application/pdf"}.get(
        ext, mimetypes.guess_type(f.name)[0] or "application/octet-stream")
    a = Attachment.objects.create(
        inspection=insp, unit_key=unit_key, file=f, original_name=os.path.basename(f.name)[:250],
        content_type=ctype, size=f.size, caption=request.POST.get("caption", "")[:250], uploaded_by=request.user,
    )
    audit.log(request, "FILE_UPLOADED", insp, unit_key, None, a.original_name, details=f"attachment {a.id}, {a.size} bytes")
    return JsonResponse({"ok": True, "attachment": {
        "id": a.id, "name": a.original_name, "size": a.size, "image": a.is_image, "caption": a.caption,
        "url": reverse("attachment_file", args=[a.id]),
        "by": request.user.get_full_name() or request.user.username, "can_delete": True,
    }})


@require_POST
@login_required
def api_delete_attachment(request, pk, att_id):
    insp = get_object_or_404(Inspection.objects.select_related("iti"), pk=pk)
    a = get_object_or_404(Attachment, pk=att_id, inspection=insp, deleted=False)
    unit = units_by_key().get(a.unit_key)
    if insp.is_locked or not unit or unit.part_key not in editable_parts(request.user, insp):
        return JsonResponse({"ok": False, "error": "Not authorised."}, status=403)
    if not (a.uploaded_by_id == request.user.id or is_leader(request.user, insp)):
        return JsonResponse({"ok": False, "error": "Only the uploader or team leader can remove this file."}, status=403)
    a.deleted = True
    a.save(update_fields=["deleted"])
    audit.log(request, "FILE_REMOVED", insp, a.unit_key, a.original_name, None, details=f"attachment {a.id}")
    return JsonResponse({"ok": True})


@login_required
def attachment_file(request, att_id):
    a = get_object_or_404(Attachment.objects.select_related("inspection"), pk=att_id)
    if not can_view(request.user, a.inspection):
        raise PermissionDenied
    if a.deleted and not is_admin(request.user):
        raise Http404
    try:
        fh = a.file.open("rb")
    except FileNotFoundError:
        raise Http404
    resp = FileResponse(fh, content_type=a.content_type)
    disp = "attachment" if request.GET.get("download") else "inline"
    resp["Content-Disposition"] = f'{disp}; filename="{a.original_name.replace(chr(34), "")}"'
    resp["Cache-Control"] = "private, max-age=600"
    return resp


@login_required
def inspection_review(request, pk):
    insp = get_object_or_404(Inspection.objects.select_related("iti"), pk=pk)
    if not insp.team.filter(user=request.user).exists():
        raise PermissionDenied
    data = insp.data or {}
    missing, invalid = services.submission_blockers(insp)
    ub = units_by_key()
    pp = part_progress(data, insp.iti.is_govt)
    parts = []
    for p in parts_list():
        if p["govt_only"] and not insp.iti.is_govt:
            continue
        d = pp.get(p["key"], {"done": 0, "total": 0})
        parts.append({**p, **d, "pct": round(100 * d["done"] / d["total"]) if d["total"] else 0})
    members = data.get("SA.J8.members") or []
    ctx = _form_context(request, insp, "view")
    ctx.update({
        "parts_summary": parts,
        "overall": progress(data, insp.iti.is_govt),
        "missing": missing,
        "invalid": [(k, ub.get(k.rsplit(".", 1)[0]) or ub.get(k), e) for k, e in invalid],
        "members": members,
        "can_submit": is_leader(request.user, insp) and not insp.is_locked,
        "unanswered": [u for u in applicable_units(insp.iti.is_govt) if not unit_answered(u, data)],
    })
    return render(request, "inspections/review.html", ctx)


@require_POST
@login_required
def inspection_submit(request, pk):
    insp = get_object_or_404(Inspection, pk=pk)
    if not is_leader(request.user, insp):
        raise PermissionDenied
    if request.POST.get("confirm") != "yes":
        messages.error(request, "Please tick the confirmation box before submitting.")
        return redirect("inspection_review", pk=pk)
    ok, msg = services.submit(request, pk)
    (messages.success if ok else messages.error)(request, msg)
    return redirect("record_view", pk=pk) if ok else redirect("inspection_review", pk=pk)


@require_POST
@login_required
def inspection_return(request, pk):
    if not is_admin(request.user):
        raise PermissionDenied
    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, "Please record the reason for returning the form.")
        return redirect("record_view", pk=pk)
    ok, msg = services.return_for_correction(request, pk, reason)
    (messages.success if ok else messages.error)(request, msg)
    return redirect("record_view", pk=pk)


@login_required
def inspection_pdf(request, pk):
    from .reports import build_pdf
    insp = get_object_or_404(Inspection.objects.select_related("iti"), pk=pk)
    if not can_view(request.user, insp):
        raise PermissionDenied
    pdf = build_pdf(insp)
    audit.log(request, "PDF_DOWNLOADED", insp)
    resp = HttpResponse(pdf, content_type="application/pdf")
    fname = f"Inspection_{insp.iti.mis_code}_{insp.scheduled_date}.pdf".replace("/", "-")
    resp["Content-Disposition"] = f'attachment; filename="{fname}"'
    return resp


@login_required
def inspection_xlsx(request, pk):
    from .exports import inspection_workbook
    insp = get_object_or_404(Inspection.objects.select_related("iti"), pk=pk)
    if not can_view(request.user, insp):
        raise PermissionDenied
    content = inspection_workbook(insp)
    audit.log(request, "EXCEL_DOWNLOADED", insp)
    resp = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    fname = f"Inspection_{insp.iti.mis_code}_{insp.scheduled_date}.xlsx".replace("/", "-")
    resp["Content-Disposition"] = f'attachment; filename="{fname}"'
    return resp


@login_required
def proforma_notes(request):
    return render(request, "inspections/proforma_notes.html", {"corrections": CORRECTIONS})


def service_worker(request):
    path = os.path.join(os.path.dirname(__file__), "static", "inspections", "sw.js")
    with open(path, "rb") as fh:
        resp = HttpResponse(fh.read(), content_type="application/javascript")
    resp["Service-Worker-Allowed"] = "/"
    resp["Cache-Control"] = "no-cache"
    return resp


def manifest(request):
    return JsonResponse({
        "name": "ITI Inspection Portal", "short_name": "ITI Inspection", "start_url": "/",
        "display": "standalone", "background_color": "#ffffff", "theme_color": "#1f3a5f",
        "icons": [{"src": "/static/inspections/icon.svg", "sizes": "any", "type": "image/svg+xml"}],
    })
