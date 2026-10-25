"""
Helpers built on the proforma schema: an index of every answerable item and
input, validation, completeness/progress, and the J2 compliance summary.
The same logic is mirrored in static/inspections/form.js for live display.
"""
import datetime
import re
from functools import lru_cache

from .proforma import PROFORMA, CPN_OPTIONS

LIST_TYPES = {"rows", "grid", "area_rows", "trades", "members"}


class Unit:
    """One answerable item of the proforma (a row / question / table)."""

    def __init__(self, key, part_key, section_id, part_code, block_id, sno, label, inputs, kind):
        self.key = key
        self.part_key = part_key
        self.section_id = section_id
        self.part_code = part_code
        self.block_id = block_id
        self.sno = sno
        self.label = label
        self.inputs = inputs  # list of input keys
        self.kind = kind

    def as_dict(self):
        return {"key": self.key, "part": self.part_key, "sno": self.sno, "label": self.label, "inputs": self.inputs}


def _row_cols(columns):
    return {c["k"]: c for c in columns}


@lru_cache(maxsize=1)
def build_index():
    """Returns (units: list[Unit], inputs: dict[input_key -> spec], parts: list[dict])."""
    units = []
    inputs = {}
    parts = []

    def add_input(key, spec, part_key, unit_key):
        spec = dict(spec)
        spec["part"] = part_key
        spec["unit"] = unit_key
        inputs[key] = spec
        return key

    for sec in PROFORMA["sections"]:
        sid = sec["id"]
        for part in sec["parts"]:
            pkey = f"{sid}.{part['code']}"
            parts.append({"key": pkey, "section": sid, "section_title": sec["title"], "code": part["code"],
                          "title": part["title"], "govt_only": part.get("govt_only", False)})
            for block in part["blocks"]:
                t = block["type"]
                bid = block.get("id", "")

                def mk(ukey, sno, label, ins, kind=t):
                    units.append(Unit(ukey, pkey, sid, part["code"], bid, sno, label, ins, kind))

                if t == "particulars":
                    for row in block["rows"]:
                        ukey = f"{sid}.{row['sno']}"
                        ins = []
                        for f in row["fields"]:
                            ikey = ukey if not f["k"] else f"{ukey}.{f['k']}"
                            if f["t"] == "rows":
                                ins.append(add_input(ikey, {"t": "rows", "columns": _row_cols(f["columns"])}, pkey, ukey))
                            else:
                                ins.append(add_input(ikey, {"t": f["t"], "options": f.get("options")}, pkey, ukey))
                        mk(ukey, row["sno"], row["text"], ins)
                elif t == "checklist":
                    for row in block["rows"]:
                        ukey = f"{sid}.{row['sno']}"
                        ins = [add_input(f"{ukey}.obs", {"t": "textarea"}, pkey, ukey),
                               add_input(f"{ukey}.cpn", {"t": "radio", "options": CPN_OPTIONS, "cpn": True}, pkey, ukey)]
                        for ex in row.get("extras", []):
                            ins.append(add_input(f"{ukey}.{ex['k']}", {"t": ex["t"]}, pkey, ukey))
                        mk(ukey, row["sno"], row["text"], ins)
                elif t == "area":
                    for row in block["rows"]:
                        ukey = f"{sid}.{row['sno']}"
                        if row.get("repeat"):
                            cols = {"trade_unit": {"t": "text"}, "measured": {"t": "text"},
                                    "cpn": {"t": "select", "options": CPN_OPTIONS}}
                            ins = [add_input(ukey, {"t": "area_rows", "columns": cols}, pkey, ukey)]
                        else:
                            ins = [add_input(f"{ukey}.measured", {"t": "text"}, pkey, ukey),
                                   add_input(f"{ukey}.cpn", {"t": "radio", "options": CPN_OPTIONS, "cpn": True}, pkey, ukey)]
                        mk(ukey, row["sno"], row["text"], ins)
                elif t == "grid":
                    ukey = f"{sid}.{bid}"
                    ins = [add_input(ukey, {"t": "grid", "columns": _row_cols(block["columns"])}, pkey, ukey)]
                    for h in block.get("header_inputs", []):
                        ins.append(add_input(f"{ukey}.hdr.{h['k']}", {"t": h["t"]}, pkey, ukey))
                    mk(ukey, bid, block["title"], ins)
                elif t == "staffing":
                    for post in block["posts"]:
                        ukey = f"{sid}.{bid}.{post['k']}"
                        ins = [add_input(f"{ukey}.{c['k']}", {"t": c["t"]}, pkey, ukey) for c in block["columns"]]
                        mk(ukey, bid, post["post"], ins)
                        if post["k"] == block.get("trade_rows_after"):
                            tkey = f"{sid}.{bid}.trades"
                            cols = {"trade": {"t": "text"}}
                            cols.update({c["k"]: {"t": c["t"]} for c in block["columns"]})
                            mk(tkey, bid, "Trade instructors — trade-wise rows",
                               [add_input(tkey, {"t": "trades", "columns": cols}, pkey, tkey)], kind="trades")
                elif t == "register":
                    for row in block["rows"]:
                        ukey = f"{sid}.{row['sno']}"
                        ins = [add_input(f"{ukey}.maint", {"t": "radio", "options": ["Y", "N"]}, pkey, ukey),
                               add_input(f"{ukey}.uptodate", {"t": "radio", "options": ["Y", "N"]}, pkey, ukey),
                               add_input(f"{ukey}.remarks", {"t": "text"}, pkey, ukey)]
                        mk(ukey, row["sno"], row["text"], ins)
                elif t == "office":
                    for row in block["rows"]:
                        ukey = f"{sid}.{row['sno']}"
                        ins = [add_input(f"{ukey}.avail", {"t": "radio", "options": ["Yes", "No"]}, pkey, ukey),
                               add_input(f"{ukey}.updated", {"t": "date"}, pkey, ukey),
                               add_input(f"{ukey}.deficiency", {"t": "textarea"}, pkey, ukey),
                               add_input(f"{ukey}.action", {"t": "textarea"}, pkey, ukey)]
                        mk(ukey, f"{row['sr']} {row['sno']}", row["text"], ins)
                elif t == "j1":
                    for row in block["rows"]:
                        ukey = f"{sid}.J1.{row['k']}"
                        ins = [add_input(f"{ukey}.found", {"t": "radio", "options": ["Y", "N"]}, pkey, ukey),
                               add_input(f"{ukey}.evidence", {"t": "textarea"}, pkey, ukey)]
                        mk(ukey, "J1", row["ground"], ins)
                elif t == "choice":
                    ukey = f"{sid}.{bid}"
                    mk(ukey, bid, block["title"], [add_input(ukey, {"t": "radio", "options": block["options"]}, pkey, ukey)])
                elif t == "text":
                    ukey = f"{sid}.{bid}"
                    mk(ukey, bid, block["title"], [add_input(ukey, {"t": "textarea"}, pkey, ukey)])
                elif t == "declaration":
                    ukey = f"{sid}.{bid}"
                    cols = {"name": {"t": "text"}, "designation": {"t": "text"}, "declared": {"t": "bool"},
                            "date": {"t": "date"}, "user_id": {"t": "int"}, "declared_at": {"t": "text"},
                            "declared_by": {"t": "text"}}
                    ins = [add_input(f"{ukey}.members", {"t": "members", "columns": cols}, pkey, ukey),
                           add_input(f"{ukey}.ack_received", {"t": "date"}, pkey, ukey),
                           add_input(f"{ukey}.atr_due", {"t": "date"}, pkey, ukey)]
                    mk(ukey, bid, block["title"], ins)
                # note / j2: nothing to answer
    return units, inputs, parts


def units_by_key():
    units, _, _ = build_index()
    return {u.key: u for u in units}


def parts_list():
    return build_index()[2]


def input_specs():
    return build_index()[1]


def part_of_key(key):
    spec = input_specs().get(key)
    return spec["part"] if spec else None


# ----------------------------------------------------------------- validation
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME = re.compile(r"^\d{2}:\d{2}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_scalar(t, v, options=None):
    """Return error string or None. Empty values are always allowed."""
    if v is None or v == "":
        return None
    if t in ("text", "textarea"):
        if not isinstance(v, str):
            return "must be text"
        if len(v) > 20000:
            return "is too long"
        return None
    if t == "number":
        try:
            n = float(v)
        except (TypeError, ValueError):
            return "must be a number"
        if n < 0:
            return "cannot be negative"
        return None
    if t == "int":
        try:
            int(v)
        except (TypeError, ValueError):
            return "must be a whole number"
        return None
    if t == "date":
        if not isinstance(v, str) or not _DATE.match(v):
            return "must be a date (YYYY-MM-DD)"
        try:
            datetime.date.fromisoformat(v)
        except ValueError:
            return "is not a valid date"
        return None
    if t == "time":
        if not isinstance(v, str) or not _TIME.match(v):
            return "must be a time (HH:MM)"
        h, m = v.split(":")
        if int(h) > 23 or int(m) > 59:
            return "is not a valid time"
        return None
    if t == "email":
        return None if isinstance(v, str) and _EMAIL.match(v) else "must be a valid e-mail address"
    if t == "tel":
        return None if isinstance(v, str) and re.fullmatch(r"[0-9+\-\s()]{6,20}", v) else "must be a valid phone number"
    if t in ("lat", "lng"):
        try:
            n = float(v)
        except (TypeError, ValueError):
            return "must be a number"
        lim = 90 if t == "lat" else 180
        return None if -lim <= n <= lim else "is out of range"
    if t in ("radio", "select"):
        return None if options and v in options else "is not one of the allowed options"
    if t == "bool":
        return None if isinstance(v, bool) else "must be true/false"
    return None


def validate_value(key, value):
    """Validate one input value. Returns error message or None."""
    spec = input_specs().get(key)
    if spec is None:
        return "unknown field"
    t = spec["t"]
    if t in LIST_TYPES:
        if value in (None, ""):
            return None
        if not isinstance(value, list):
            return "must be a list of rows"
        if len(value) > 500:
            return "has too many rows"
        cols = spec["columns"]
        for i, row in enumerate(value):
            if not isinstance(row, dict):
                return f"row {i + 1} is invalid"
            for ck, cv in row.items():
                if ck not in cols:
                    return f"row {i + 1}: unknown column {ck}"
                err = _check_scalar(cols[ck]["t"], cv, cols[ck].get("options"))
                if err:
                    return f"row {i + 1}, {ck} {err}"
        return None
    return _check_scalar(t, value, spec.get("options"))


# --------------------------------------------------------------- completeness
def _filled(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, list):
        return any(_row_filled(r) for r in v)
    return True


def _row_filled(r):
    if not isinstance(r, dict):
        return False
    return any(_filled(v) for k, v in r.items() if k not in ("user_id",))


def unit_answered(unit, data):
    if unit.kind == "declaration":
        members = data.get(f"{unit.key}.members") or []
        return any(isinstance(m, dict) and m.get("declared") for m in members)
    return any(_filled(data.get(k)) for k in unit.inputs)


def applicable_units(iti_is_govt=True):
    units, _, parts = build_index()
    govt_only = {p["key"] for p in parts if p["govt_only"]}
    return [u for u in units if iti_is_govt or u.part_key not in govt_only]


def progress(data, iti_is_govt=True, part_keys=None):
    us = applicable_units(iti_is_govt)
    if part_keys:
        us = [u for u in us if u.part_key in part_keys]
    total = len(us)
    done = sum(1 for u in us if unit_answered(u, data))
    return {"done": done, "total": total, "pct": round(100 * done / total) if total else 0}


def part_progress(data, iti_is_govt=True):
    out = {}
    for u in applicable_units(iti_is_govt):
        d = out.setdefault(u.part_key, {"done": 0, "total": 0})
        d["total"] += 1
        if unit_answered(u, data):
            d["done"] += 1
    return out


def missing_mandatory(data, mandatory_keys, iti_is_govt=True):
    ub = {u.key: u for u in applicable_units(iti_is_govt)}
    return [ub[k] for k in mandatory_keys if k in ub and not unit_answered(ub[k], data)]


def invalid_values(data):
    errors = []
    for k, v in data.items():
        err = validate_value(k, v)
        if err and err != "unknown field":
            errors.append((k, err))
    return errors


# --------------------------------------------------------------------- J2
def j2_summary(data):
    """Compute J2 counts from C/P/N/NA responses in Section A."""
    from .proforma import J2_ROWS
    units, _, _ = build_index()
    by_block = {}
    for u in units:
        if u.section_id == "SA":
            by_block.setdefault(u.block_id, []).append(u)
    rows = []
    totals = {"checked": 0, "C": 0, "P": 0, "N": 0, "NA": 0}
    for code, label, blocks in J2_ROWS:
        c = {"checked": 0, "C": 0, "P": 0, "N": 0, "NA": 0}
        for b in blocks:
            for u in by_block.get(b, []):
                for val in _cpn_values(u, data):
                    if val in ("C", "P", "N", "NA"):
                        c[val] += 1
                        c["checked"] += 1
        rows.append({"code": code, "label": label, **c})
        for k in totals:
            totals[k] += c[k]
    rows.append({"code": "Total", "label": "Total", **totals})
    return rows


def _cpn_values(u, data):
    if u.kind == "register":
        m = data.get(f"{u.key}.maint")
        up = data.get(f"{u.key}.uptodate")
        if m == "Y" and up == "Y":
            return ["C"]
        if m == "Y" and up == "N":
            return ["P"]
        if m == "N":
            return ["N"]
        return []
    if u.kind == "area" and isinstance(data.get(u.key), list):
        return [r.get("cpn") for r in data.get(u.key) if isinstance(r, dict)]
    v = data.get(f"{u.key}.cpn")
    return [v] if v else []


def pct(passed, appeared):
    try:
        a = float(appeared)
        p = float(passed)
    except (TypeError, ValueError):
        return ""
    if a <= 0:
        return ""
    return round(100 * p / a, 1)
