"""PDF of the completed inspection proforma (ReportLab)."""
import io
import os

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table as RLTable, TableStyle)
from xml.sax.saxutils import escape

from .proforma import PROFORMA, CORRECTIONS
from .services import team_rows
from .tables import LEGENDS, build, fmt

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
_registered = False


def _fonts():
    global _registered
    if _registered:
        return
    pdfmetrics.registerFont(TTFont("DV", os.path.join(FONT_DIR, "DejaVuSansCondensed.ttf")))
    pdfmetrics.registerFont(TTFont("DVB", os.path.join(FONT_DIR, "DejaVuSansCondensed-Bold.ttf")))
    pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")
    _registered = True


NAVY = colors.HexColor("#1f3a5f")
GRID = colors.HexColor("#9aa9bd")
HEAD_BG = colors.HexColor("#e8edf4")


def _styles():
    return {
        "title": ParagraphStyle("title", fontName="DVB", fontSize=15, leading=19, alignment=TA_CENTER, textColor=NAVY, spaceAfter=2),
        "subtitle": ParagraphStyle("subtitle", fontName="DV", fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#3d4a5c")),
        "section": ParagraphStyle("section", fontName="DVB", fontSize=12, leading=15, textColor=colors.white, backColor=NAVY,
                                  borderPadding=(4, 6, 4, 6), spaceBefore=6, spaceAfter=8),
        "part": ParagraphStyle("part", fontName="DVB", fontSize=11, leading=14, textColor=NAVY, spaceBefore=8, spaceAfter=4),
        "block": ParagraphStyle("block", fontName="DVB", fontSize=9, leading=11.5, textColor=colors.HexColor("#2c5282"), spaceBefore=6, spaceAfter=3),
        "cell": ParagraphStyle("cell", fontName="DV", fontSize=8, leading=9.8),
        "head": ParagraphStyle("head", fontName="DVB", fontSize=7.8, leading=9.5),
        "note": ParagraphStyle("note", fontName="DV", fontSize=8, leading=10, textColor=colors.HexColor("#3d4a5c"), spaceBefore=2, spaceAfter=4),
        "para": ParagraphStyle("para", fontName="DV", fontSize=8.8, leading=11.5, spaceBefore=4, spaceAfter=4),
        "warn": ParagraphStyle("warn", fontName="DVB", fontSize=10, leading=13, textColor=colors.HexColor("#b42318"), alignment=TA_CENTER),
    }


def _p(text, style):
    return Paragraph(escape(text or "").replace("\n", "<br/>"), style)


def _table(tb, st, avail):
    ncol = len(tb.headers)
    widths = tb.widths if tb.widths and len(tb.widths) == ncol else None
    if not widths:
        # Generic grid: first column wider, others equal.
        widths = [100 / ncol] * ncol
        if ncol > 2:
            widths = [max(14, 100 / ncol * 1.6)] + [(100 - max(14, 100 / ncol * 1.6)) / (ncol - 1)] * (ncol - 1)
    total = sum(widths)
    colw = [avail * w / total for w in widths]
    data = []
    has_head = any(h for h in tb.headers)
    if has_head:
        data.append([_p(h, st["head"]) for h in tb.headers])
    for r in tb.rows:
        data.append([_p(c, st["cell"]) for c in r])
    t = RLTable(data, colWidths=colw, repeatRows=1 if has_head else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]
    if has_head:
        style.append(("BACKGROUND", (0, 0), (-1, 0), HEAD_BG))
    if tb.rows and tb.rows[-1] and tb.rows[-1][0] == "Total":
        style.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f2f4f7")))
    t.setStyle(TableStyle(style))
    return t


def _thumb(att, max_w, max_h):
    from PIL import Image as PILImage
    try:
        with att.file.open("rb") as fh:
            im = PILImage.open(fh)
            im.load()
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.thumbnail((1400, 1400))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        buf.seek(0)
        w, h = im.size
        scale = min(max_w / w, max_h / h, 1)
        return Image(buf, width=w * scale, height=h * scale)
    except Exception:  # noqa: BLE001
        return None


def build_pdf(insp):
    _fonts()
    st = _styles()
    buf = io.BytesIO()
    page_w, page_h = A4
    margin = 13 * mm
    submitted = insp.status == "SUBMITTED"
    header_text = f"{PROFORMA['title']} — {insp.iti.name} ({insp.iti.mis_code})"

    def on_page(canvas, doc, landscape_mode=False):
        w, h = canvas._pagesize
        canvas.saveState()
        canvas.setFont("DV", 7.5)
        canvas.setFillColor(colors.HexColor("#5d6b7c"))
        canvas.drawString(margin, h - 8 * mm, header_text[:140])
        canvas.drawRightString(w - margin, 7 * mm, f"Page {doc.page}")
        canvas.drawString(margin, 7 * mm, f"Generated {timezone.localtime().strftime('%d-%m-%Y %H:%M')} · "
                                          f"Status: {insp.get_status_display()}")
        if not submitted:
            canvas.setFont("DVB", 46)
            canvas.setFillColor(colors.Color(0.85, 0.2, 0.2, alpha=0.12))
            canvas.translate(w / 2, h / 2)
            canvas.rotate(35)
            canvas.drawCentredString(0, 0, "DRAFT — NOT SUBMITTED")
        canvas.restoreState()

    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=13 * mm, bottomMargin=12 * mm,
                          title=f"Inspection — {insp.iti.name}", author="DTE Himachal Pradesh — ITI Inspection Portal")
    portrait_frame = Frame(margin, 12 * mm, page_w - 2 * margin, page_h - 25 * mm, id="p")
    lw, lh = landscape(A4)
    land_frame = Frame(margin, 12 * mm, lw - 2 * margin, lh - 25 * mm, id="l")
    doc.addPageTemplates([
        PageTemplate(id="portrait", frames=[portrait_frame], onPage=on_page, pagesize=A4),
        PageTemplate(id="landscape", frames=[land_frame], onPage=on_page, pagesize=landscape(A4)),
    ])
    avail_p = page_w - 2 * margin
    avail_l = lw - 2 * margin

    atts = {}
    for a in insp.attachments.filter(deleted=False).select_related("uploaded_by"):
        atts.setdefault(a.unit_key, []).append(a)

    story = []
    story.append(_p(PROFORMA["title"], st["title"]))
    story.append(_p("Directorate of Technical Education, Vocational & Industrial Training, Himachal Pradesh", st["subtitle"]))
    story.append(Spacer(1, 6))
    if not submitted:
        story.append(_p("DRAFT — this inspection has not been submitted. Entries may change.", st["warn"]))
        story.append(Spacer(1, 4))
    team = team_rows(insp)
    leader = next((t for t in team if t["role"] == "LEADER"), None)
    info = [
        ["Name of ITI", insp.iti.name, "MIS code", insp.iti.mis_code],
        ["District", insp.iti.district, "Ownership", insp.iti.get_ownership_display()],
        ["Inspection team", insp.team_name, "Team leader", leader["name"] if leader else ""],
        ["Team members", ", ".join(t["name"] for t in team if t["role"] != "LEADER") or "—", "Scheduled visit", insp.scheduled_date.strftime("%d-%m-%Y")],
        ["Date of inspection", fmt((insp.data or {}).get("SA.A7.date"), "date"), "Submission deadline", insp.deadline.strftime("%d-%m-%Y")],
        ["Submission status", insp.get_status_display(), "Submitted on / by",
         (timezone.localtime(insp.submitted_at).strftime("%d-%m-%Y %H:%M") + " / " + (insp.submitted_by.get_full_name() or insp.submitted_by.username))
         if insp.submitted_at and insp.submitted_by else "—"],
    ]
    it = RLTable([[_p(c, st["head"] if i % 2 == 0 else st["cell"]) for i, c in enumerate(r)] for r in info],
                 colWidths=[avail_p * x for x in (0.17, 0.33, 0.17, 0.33)])
    it.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, GRID), ("BACKGROUND", (0, 0), (0, -1), HEAD_BG),
                            ("BACKGROUND", (2, 0), (2, -1), HEAD_BG), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(it)
    story.append(Spacer(1, 4))
    for lg in LEGENDS:
        story.append(_p(lg, st["note"]))

    last_section = None
    current_tpl = "portrait"
    for sec_title, part_title, els in build(insp, atts):
        wide = any(e[0] == "table" and len(e[1].headers) >= 9 for e in els)
        want = "landscape" if wide else "portrait"
        if want != current_tpl:
            story.append(NextPageTemplate(want))
            story.append(PageBreak())
            current_tpl = want
        avail = avail_l if current_tpl == "landscape" else avail_p
        if sec_title != last_section:
            if last_section is not None and want == current_tpl and story and not isinstance(story[-1], PageBreak):
                story.append(PageBreak())
            story.append(_p(sec_title, st["section"]))
            last_section = sec_title
        story.append(CondPageBreak(40 * mm))
        story.append(_p(part_title, st["part"]))
        for e in els:
            if e[0] == "table":
                tb = e[1]
                parts = []
                if tb.title:
                    parts.append(_p(tb.title, st["block"]))
                parts.append(_table(tb, st, avail))
                if len(tb.rows) <= 6:
                    story.append(KeepTogether(parts))
                else:
                    story.extend(parts)
            elif e[0] == "note":
                story.append(_p(e[1], st["note"]))
            elif e[0] == "para":
                story.append(_p(e[1], st["para"]))
    if current_tpl != "portrait":
        story.append(NextPageTemplate("portrait"))
    story.append(PageBreak())

    # Annexure: evidence
    story.append(_p("Annexure — Photographs and supporting documents", st["section"]))
    all_atts = [a for lst in atts.values() for a in lst]
    if not all_atts:
        story.append(_p("No photographs or documents were uploaded.", st["para"]))
    else:
        from .schema import units_by_key
        ub = units_by_key()
        order = {u: i for i, u in enumerate(ub.keys())}
        for unit_key in sorted(atts.keys(), key=lambda k: order.get(k, 99999)):
            u = ub.get(unit_key)
            label = f"{u.sno} — {u.label}" if u and u.sno and u.sno not in u.label else (u.label if u else unit_key)
            story.append(CondPageBreak(50 * mm))
            story.append(_p(f"{unit_key.split('.')[0].replace('SA', 'Section A').replace('SB', 'Section B')} · {label}", st["block"]))
            for a in atts[unit_key]:
                meta = (f"{a.original_name} · {round(a.size / 1024)} KB · uploaded {timezone.localtime(a.uploaded_at).strftime('%d-%m-%Y %H:%M')}"
                        f"{' by ' + (a.uploaded_by.get_full_name() or a.uploaded_by.username) if a.uploaded_by else ''}"
                        f"{' · ' + a.caption if a.caption else ''}")
                img = _thumb(a, 85 * mm, 70 * mm) if a.is_image else None
                if img:
                    story.append(KeepTogether([img, _p(meta, st["note"])]))
                else:
                    story.append(_p("Document (not embedded): " + meta, st["note"]))
    story.append(Spacer(1, 10))
    story.append(_p("Notes on the digital proforma", st["block"]))
    for c in CORRECTIONS:
        story.append(_p("• " + c, st["note"]))

    doc.build(story)
    return buf.getvalue()
