"""
Builds the completed proforma as a sequence of titled tables that mirror the
printed proforma. Used by the PDF report and the per-inspection Excel file.
"""
import datetime

from .proforma import PROFORMA, STAR_LEGEND, CPN_LEGEND
from .schema import j2_summary, pct


def fmt(v, t=None):
    if v is None or v == "":
        return ""
    if t == "date" and isinstance(v, str) and len(v) == 10:
        try:
            return datetime.date.fromisoformat(v).strftime("%d-%m-%Y")
        except ValueError:
            return v
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _row_filled(r):
    return isinstance(r, dict) and any(v not in (None, "", False) for k, v in r.items() if k != "user_id")


def _att_note(unit_key, atts):
    n = len(atts.get(unit_key, []))
    return f"[{n} attachment{'s' if n > 1 else ''} — see Annexure]" if n else ""


def _join(*parts):
    return "\n".join(p for p in parts if p)


class Table:
    def __init__(self, title, headers, rows, widths=None, kind="table", unit_keys=None):
        self.title = title
        self.headers = headers
        self.rows = rows
        self.widths = widths  # relative widths
        self.kind = kind
        self.unit_keys = unit_keys or []


def build(insp, attachments_by_unit=None):
    """Return list of (section_title, part_title, [elements]) where element is
    ("table", Table) | ("para", text) | ("note", text)."""
    data = insp.data or {}
    atts = attachments_by_unit or {}
    out = []
    for sec in PROFORMA["sections"]:
        sid = sec["id"]
        for part in sec["parts"]:
            els = []
            if part.get("govt_only") and not insp.iti.is_govt:
                els.append(("note", "Not applicable — this part applies to Government ITIs only."))
                out.append((sec["title"], part["title"], els))
                continue
            for b in part["blocks"]:
                t = b["type"]
                title = b.get("title", "")
                if t == "note":
                    els.append(("note", b["text"]))
                elif t == "particulars":
                    rows = []
                    for r in b["rows"]:
                        uk = f"{sid}.{r['sno']}"
                        lines = []
                        for f in r["fields"]:
                            key = uk if not f["k"] else f"{uk}.{f['k']}"
                            v = data.get(key)
                            if f["t"] == "rows":
                                for i, row in enumerate([x for x in (v or []) if _row_filled(x)], 1):
                                    lines.append(f"{i}. " + "; ".join(
                                        f"{c['label']}: {fmt(row.get(c['k']), c['t'])}" for c in f["columns"] if fmt(row.get(c["k"]))))
                            else:
                                val = fmt(v, f["t"])
                                if f.get("label"):
                                    lines.append(f"{f['label']}: {val}")
                                else:
                                    lines.append(val)
                        rows.append([r["sno"], r["text"], _join(*lines, _att_note(uk, atts))])
                    els.append(("table", Table(title, ["S.No", "Particulars", "Details"], rows, [8, 42, 50])))
                elif t == "checklist":
                    rows = []
                    for r in b["rows"]:
                        uk = f"{sid}.{r['sno']}"
                        extras = "; ".join(f"{x['label']}: {('Rs ' if x.get('unit') == 'Rs' else '')}{fmt(data.get(uk + '.' + x['k']), x['t'])}"
                                           f"{(' ' + x['unit']) if x.get('unit') and x['unit'] != 'Rs' else ''}"
                                           for x in r.get("extras", []) if fmt(data.get(uk + "." + x["k"])))
                        observed = _join(extras, fmt(data.get(uk + ".obs")), _att_note(uk, atts))
                        text = ("★ " if r.get("star") else "") + r["text"]
                        if b.get("no_norm"):
                            rows.append([r["sno"], text, observed, fmt(data.get(uk + ".cpn"))])
                        else:
                            rows.append([r["sno"], text, r["norm"], observed, fmt(data.get(uk + ".cpn"))])
                    if b.get("no_norm"):
                        els.append(("table", Table(title, ["S.No", "Item to verify", "Observed", "C/P/N"], rows, [8, 50, 34, 8])))
                    else:
                        els.append(("table", Table(title, ["S.No", "Item to verify", "Norm / Ref", "Observed", "C/P/N"], rows, [8, 33, 25, 26, 8])))
                elif t == "area":
                    rows = []
                    for r in b["rows"]:
                        uk = f"{sid}.{r['sno']}"
                        if r.get("repeat"):
                            sub = [x for x in (data.get(uk) or []) if _row_filled(x)]
                            if not sub:
                                rows.append([r["sno"], r["text"], r["norm"], _att_note(uk, atts), ""])
                            for i, x in enumerate(sub):
                                rows.append([r["sno"] if i == 0 else "", (r["text"] + "\n" if i == 0 else "") + "— " + fmt(x.get("trade_unit")),
                                             r["norm"] if i == 0 else "", _join(fmt(x.get("measured")), _att_note(uk, atts) if i == 0 else ""),
                                             fmt(x.get("cpn"))])
                        else:
                            rows.append([r["sno"], r["text"], r["norm"], _join(fmt(data.get(uk + ".measured")), _att_note(uk, atts)),
                                         fmt(data.get(uk + ".cpn"))])
                    els.append(("table", Table(title, ["S.No", "Space", "Minimum norm", "Measured area / count", "C/P/N"], rows, [8, 22, 40, 22, 8])))
                    if b.get("footnote"):
                        els.append(("note", b["footnote"]))
                elif t == "grid":
                    uk = f"{sid}.{b['id']}"
                    hdr = {h["k"]: data.get(f"{uk}.hdr.{h['k']}") or "___" for h in b.get("header_inputs", [])}
                    cols = b["columns"]
                    headers = []
                    for c in cols:
                        lab = c["label"]
                        if c.get("group"):
                            lab = lab.replace("(1)", "").replace("(2)", "").replace("(3)", "")
                            lab = lab.replace("Session :", f"Session {hdr.get(c['group'])}:").replace("Year :", f"Year {hdr.get(c['group'])}:")
                        headers.append(lab)
                    rows = []
                    src = [x for x in (data.get(uk) or []) if _row_filled(x)]
                    if not src:
                        src = [dict(x) for x in b.get("initial_rows", [])] or ([dict(b["fixed_first"])] if b.get("fixed_first") else [])
                    for i, row in enumerate(src, 1):
                        cells = []
                        for c in cols:
                            v = row.get(c["k"])
                            if c.get("calc"):
                                v = pct(row.get(c["calc"][1]), row.get(c["calc"][2]))
                            cells.append(fmt(v, c["t"]))
                        rows.append(([str(i)] if b.get("numbered") else []) + cells)
                    if not rows:
                        rows.append(([""] if b.get("numbered") else []) + [""] * len(cols))
                    if b.get("numbered"):
                        headers = ["S.No"] + headers
                    note = _att_note(uk, atts)
                    tb = Table(title, headers, rows)
                    els.append(("table", tb))
                    if note:
                        els.append(("note", note))
                elif t == "staffing":
                    rows = []
                    for p in b["posts"]:
                        uk = f"{sid}.{b['id']}.{p['k']}"
                        rows.append([p["post"], p["norm"]] + [fmt(data.get(f"{uk}.{c['k']}")) for c in b["columns"]])
                        if p["k"] == b.get("trade_rows_after"):
                            for tr in [x for x in (data.get(f"{sid}.{b['id']}.trades") or []) if _row_filled(x)]:
                                rows.append(["   — " + fmt(tr.get("trade")), ""] + [fmt(tr.get(c["k"])) for c in b["columns"]])
                    els.append(("table", Table(title, ["Post", "Norm"] + [c["label"] for c in b["columns"]], rows, [22, 28, 12, 10, 10, 18])))
                elif t == "register":
                    rows = []
                    for r in b["rows"]:
                        uk = f"{sid}.{r['sno']}"
                        rows.append([r["sno"], r["text"], r["norm"], fmt(data.get(uk + ".maint")), fmt(data.get(uk + ".uptodate")),
                                     _join(fmt(data.get(uk + ".remarks")), _att_note(uk, atts))])
                    els.append(("table", Table(title, ["S.No", "Register / record", "Ref", "Maintained (Y/N)", "Up to date (Y/N)", "Remarks"], rows, [8, 34, 18, 10, 10, 20])))
                elif t == "office":
                    rows = []
                    for r in b["rows"]:
                        uk = f"{sid}.{r['sno']}"
                        rows.append([r["sr"], r["sno"], r["text"], r["norm"], fmt(data.get(uk + ".avail")),
                                     fmt(data.get(uk + ".updated"), "date"), fmt(data.get(uk + ".deficiency")),
                                     _join(fmt(data.get(uk + ".action")), _att_note(uk, atts))])
                    els.append(("table", Table(title, ["Sr. No.", "No.", "Head / Register", "Rule / Para", "Available (Yes/No)", "Updated up to", "Deficiency observed", "Action required"], rows, [6, 5, 19, 22, 9, 10, 15, 14])))
                elif t == "j1":
                    rows = []
                    for r in b["rows"]:
                        uk = f"{sid}.J1.{r['k']}"
                        rows.append([r["ground"], r["linked"], fmt(data.get(uk + ".found")), _join(fmt(data.get(uk + ".evidence")), _att_note(uk, atts))])
                    els.append(("table", Table(title, ["Ground (AN 7.2)", "Linked items", "Found (Y/N)", "Evidence (photo / video timestamp / document)"], rows, [36, 22, 10, 32])))
                elif t == "j2":
                    rows = [[r["label"], str(r["checked"]), str(r["C"]), str(r["P"]), str(r["N"]), str(r["NA"])] for r in j2_summary(data)]
                    els.append(("table", Table(title, ["Part", "Items checked", "C", "P", "N", "NA"], rows, [40, 15, 11, 11, 11, 12])))
                elif t == "choice":
                    uk = f"{sid}.{b['id']}"
                    sel = data.get(uk)
                    els.append(("table", Table(title, ["", "Option"], [["☑" if sel == o else "☐", o] for o in b["options"]], [6, 94], kind="choice")))
                elif t == "text":
                    uk = f"{sid}.{b['id']}"
                    els.append(("table", Table(title, [""], [[_join(fmt(data.get(uk)), _att_note(uk, atts)) or "…"]], [100], kind="text")))
                elif t == "declaration":
                    uk = f"{sid}.{b['id']}"
                    els.append(("para", title))
                    els.append(("note", b["text"]))
                    rows = []
                    members = [m for m in (data.get(uk + ".members") or []) if isinstance(m, dict)]
                    for i, m in enumerate(members, 1):
                        sig = f"Declared electronically on {m.get('declared_at')}" if m.get("declared") else ""
                        rows.append([str(i), fmt(m.get("name")), fmt(m.get("designation")), sig, fmt(m.get("date"), "date")])
                    for i in range(len(rows) + 1, 4):
                        rows.append([str(i), "", "", "", ""])
                    els.append(("table", Table("", ["Member", "Name", "Designation and office", "Signature", "Date"], rows, [9, 24, 30, 24, 13])))
                    rec = fmt(data.get(uk + ".ack_received"), "date") or "________"
                    atr = fmt(data.get(uk + ".atr_due"), "date") or "________"
                    els.append(("para", f"Acknowledgement by Principal: received a copy of this inspection report on {rec}. "
                                        f"Action Taken Report will be submitted by {atr}."))
                    els.append(("para", "Signature and seal of Principal: ____________________"))
                    note = _att_note(uk, atts)
                    if note:
                        els.append(("note", note))
            out.append((sec["title"], part["title"], els))
    return out


LEGENDS = [CPN_LEGEND, STAR_LEGEND]
