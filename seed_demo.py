"""Create sample users, ITIs and inspections for training and testing.

    python manage.py seed_demo            # adds sample data
    python manage.py seed_demo --reset    # removes earlier sample data first

All sample records are clearly marked "(Sample)". Do not run on the live server
except to train staff; remove with --reset afterwards.
"""
import datetime
import io
import random

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from inspections.models import ITI, Attachment, AuditLog, Inspection, Profile, TeamMember
from inspections.proforma import CPN_OPTIONS, J5_OPTIONS
from inspections.schema import build_index, progress
from inspections.services import seed_prefill

User = get_user_model()
PASSWORD = "Sample@2026pass"

ITIS = [
    ("SAMPLE-001", "Govt. ITI Sundernagar (Sample)", "Mandi", "Sundernagar", "GOVT"),
    ("SAMPLE-002", "Govt. ITI Mandi (Sample)", "Mandi", "Sadar", "GOVT"),
    ("SAMPLE-003", "Govt. ITI Shamshi (Sample)", "Kullu", "Kullu", "GOVT"),
    ("SAMPLE-004", "Govt. ITI Shimla (Sample)", "Shimla", "Shimla", "GOVT"),
    ("SAMPLE-005", "Govt. ITI Nalagarh (Sample)", "Solan", "Nalagarh", "GOVT"),
    ("SAMPLE-006", "Govt. ITI Dharamshala (Sample)", "Kangra", "Dharamshala", "GOVT"),
    ("SAMPLE-007", "Govt. ITI Reckong Peo (Sample)", "Kinnaur", "Kalpa", "GOVT"),
    ("SAMPLE-008", "Govt. ITI Hamirpur (Sample)", "Hamirpur", "Hamirpur", "GOVT"),
    ("SAMPLE-009", "Pvt. ITI Baddi (Sample)", "Solan", "Baddi", "PRIVATE"),
    ("SAMPLE-010", "Govt. ITI Chamba (Sample)", "Chamba", "Chamba", "GOVT"),
]

USERS = [
    ("sample.admin", "Sample Administrator", Profile.ADMIN, "Deputy Director", "DTE, Sundernagar"),
    ("sample.viewer", "Sample Monitoring Officer", Profile.VIEWER, "Assistant Director", "DTE, Sundernagar"),
    ("sample.lead1", "Anil Sharma", Profile.INSPECTOR, "Principal", "Govt. ITI Jogindernagar"),
    ("sample.mem1", "Ritu Thakur", Profile.INSPECTOR, "Group Instructor", "Govt. ITI Mandi"),
    ("sample.mem2", "Vikas Kumar", Profile.INSPECTOR, "Superintendent Gr. II", "DTE, Sundernagar"),
    ("sample.lead2", "Neha Verma", Profile.INSPECTOR, "Principal", "Govt. ITI Bilaspur"),
    ("sample.mem3", "Sanjay Negi", Profile.INSPECTOR, "Instructor (Electrician)", "Govt. ITI Shimla"),
    ("sample.lead3", "Rajesh Chauhan", Profile.INSPECTOR, "Vice-Principal", "Govt. ITI Solan"),
]


def _photo(text, color):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (1200, 800), color)
    d = ImageDraw.Draw(im)
    for i in range(0, 1200, 60):
        d.line([(i, 0), (i + 400, 800)], fill=(255, 255, 255), width=2)
    d.rectangle([60, 300, 1140, 500], fill=(255, 255, 255))
    d.text((90, 380), text, fill=(30, 50, 80))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def full_sample_data(insp, rnd, completeness=1.0):
    """Fill the form with plausible sample answers for every item (or a share of them)."""
    units, inputs, _ = build_index()
    data = dict(insp.data or {})
    text_samples = ["Verified on site; records produced.", "Board displayed at entrance.", "Partly available; to be completed.",
                    "Seen in office file.", "Not available at the time of visit.", "As per norms."]
    for u in units:
        if u.part_key == "SB.F" and not insp.iti.is_govt:
            continue
        if rnd.random() > completeness:
            continue
        for key in u.inputs:
            spec = inputs[key]
            t = spec["t"]
            if key in data and data[key]:
                continue
            if t == "radio":
                opts = spec["options"]
                if spec.get("cpn"):
                    data[key] = rnd.choices(CPN_OPTIONS, weights=[6, 2, 1, 1])[0]
                elif key == "SA.J5":
                    data[key] = J5_OPTIONS[1]
                else:
                    data[key] = rnd.choice(opts)
            elif t == "textarea":
                if key.endswith(".obs") and rnd.random() < 0.5:
                    continue
                data[key] = rnd.choice(text_samples) if not key.startswith("SA.J") else \
                    "Trainees and instructors interacted with; workshops functional. Minor deficiencies noted in J3."
            elif t == "text":
                data[key] = {"SA.A12.hours": "9:30 am to 5:00 pm", "SA.A12.shifts": "Single shift",
                             "SA.A13.score": "6.8", "SA.A13.grade": "B"}.get(key, "As observed")
            elif t == "number":
                data[key] = rnd.randint(1, 60)
            elif t == "date":
                data[key] = (insp.scheduled_date - datetime.timedelta(days=rnd.randint(0, 300))).isoformat()
            elif t == "time":
                data[key] = rnd.choice(["10:15", "16:40"])
            elif t == "lat":
                data[key] = 31.53 + rnd.random() / 100
            elif t == "lng":
                data[key] = 76.89 + rnd.random() / 100
            elif t in ("grid", "rows", "area_rows", "trades"):
                cols = spec["columns"]
                rows = []
                for i in range(rnd.randint(2, 3)):
                    row = {}
                    for ck, c in cols.items():
                        if c["t"] == "number":
                            row[ck] = rnd.randint(1, 30)
                        elif c["t"] in ("select", "radio"):
                            row[ck] = rnd.choice(c["options"])
                        elif c["t"] == "date":
                            row[ck] = "2019-07-01"
                        else:
                            row[ck] = {"trade": ["Electrician", "Fitter", "COPA", "Welder"][i % 4],
                                       "trade_unit": ["Electrician / U1", "Fitter / U1", "COPA / U1"][i % 3],
                                       "name": ["Instructor A", "Instructor B", "Instructor C"][i % 3]}.get(ck, "Sample entry")
                    rows.append(row)
                if key == "SA.E2":
                    rows[0]["post"] = "Principal"
                if key == "SA.G1":
                    for r in rows:
                        r["y1_pass"] = min(r["y1_pass"], r["y1_app"])
                        r["y2_pass"] = min(r["y2_pass"], r["y2_app"])
                        r["y3_pass"] = min(r["y3_pass"], r["y3_app"])
                data[key] = rows
            if key.startswith("SA.F1.hdr"):
                data[key] = {"s1": "2023-24", "s2": "2024-25", "s3": "2025-26"}[key[-2:]]
            if key.startswith("SA.G1.hdr"):
                data[key] = {"y1": "2023", "y2": "2024", "y3": "2025"}[key[-2:]]
    data["SA.A4"] = "Yes"
    data["SA.A6"] = "Periodic"
    data["SA.A7.date"] = insp.scheduled_date.isoformat()
    for k in [k for k in data if k.startswith("SA.J1.") and k.endswith(".found")]:
        data[k] = "N"
    return data


class Command(BaseCommand):
    help = "Create sample users, ITIs and inspections (marked 'Sample') for testing and training."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete earlier sample data first.")
        parser.add_argument("--if-empty", action="store_true", help="Do nothing if sample data already exists.")

    def handle(self, *args, **opts):
        if opts.get("if_empty") and ITI.objects.filter(mis_code__startswith="SAMPLE-").exists():
            self.stdout.write("Sample data already present; nothing to do.")
            return
        if opts["reset"]:
            from django.db.models import Q
            qs = Inspection.objects.filter(Q(iti__mis_code__startswith="SAMPLE-") | Q(team__user__username__startswith="sample.")).distinct()
            AuditLog.objects.filter(inspection__in=qs).delete()
            qs.delete()
            ITI.objects.filter(mis_code__startswith="SAMPLE-").delete()
            User.objects.filter(username__startswith="sample.").delete()
            self.stdout.write("Earlier sample data removed.")
        rnd = random.Random(42)
        users = {}
        for uname, full, role, desig, office in USERS:
            u, _ = User.objects.get_or_create(username=uname)
            first, last = (full.split(" ", 1) + [""])[:2]
            u.first_name, u.last_name = first, last
            u.email = f"{uname}@example.invalid"
            u.set_password(PASSWORD)
            u.save()
            p, _ = Profile.objects.get_or_create(user=u)
            p.role, p.designation, p.office, p.mobile = role, desig, office, "98160" + str(10000 + len(users))
            p.must_change_password = False
            p.save()
            users[uname] = u
        itis = {}
        for code, name, district, block, own in ITIS:
            iti, _ = ITI.objects.update_or_create(mis_code=code, defaults={
                "name": name, "district": district, "block": block, "ownership": own,
                "address": f"{block}, District {district}, Himachal Pradesh", "principal_name": "Principal (Sample)",
                "principal_mobile": "9816000000", "principal_email": "principal@example.invalid"})
            itis[code] = iti
        today = timezone.localdate()
        plan = [
            # code, team, leader, members, days offset visit, deadline offset, scenario
            ("SAMPLE-001", "Team 1 — Mandi", "sample.lead1", ["sample.mem1", "sample.mem2"], -6, -1, "submitted"),
            ("SAMPLE-002", "Team 1 — Mandi", "sample.lead1", ["sample.mem1", "sample.mem2"], -2, 3, "progress"),
            ("SAMPLE-003", "Team 1 — Mandi", "sample.lead1", ["sample.mem1"], 2, 7, "new"),
            ("SAMPLE-004", "Team 2 — Shimla", "sample.lead2", ["sample.mem3"], -9, -3, "overdue"),
            ("SAMPLE-005", "Team 2 — Shimla", "sample.lead2", ["sample.mem3"], -5, 1, "returned"),
            ("SAMPLE-006", "Team 3 — Kangra", "sample.lead3", [], -4, 2, "progress_low"),
            ("SAMPLE-007", "Team 2 — Shimla", "sample.lead2", ["sample.mem3"], 5, 10, "new"),
            ("SAMPLE-008", "Team 3 — Kangra", "sample.lead3", [], -8, -2, "submitted"),
            ("SAMPLE-009", "Team 3 — Kangra", "sample.lead3", [], 1, 6, "new"),
            ("SAMPLE-010", "Team 3 — Kangra", "sample.lead3", [], -12, -6, "overdue_started"),
        ]
        for code, team, lead, members, vd, dd, scenario in plan:
            iti = itis[code]
            insp, created = Inspection.objects.get_or_create(
                iti=iti, scheduled_date=today + datetime.timedelta(days=vd),
                defaults={"team_name": team, "deadline": today + datetime.timedelta(days=dd), "created_by": users["sample.admin"]})
            if not created:
                continue
            TeamMember.objects.create(inspection=insp, user=users[lead], role=TeamMember.LEADER)
            for m in members:
                TeamMember.objects.create(inspection=insp, user=users[m], role=TeamMember.MEMBER)
            if code == "SAMPLE-001":
                tm = insp.team.get(user=users["sample.mem2"])
                tm.sections = ["SB.A", "SB.B", "SB.C", "SB.D", "SB.E", "SB.F", "SB.G"]
                tm.save()
            seed_prefill(insp, refresh_team=True)
            if scenario in ("submitted", "returned"):
                insp.data = full_sample_data(insp, rnd)
                members_rows = insp.data.get("SA.J8.members", [])
                for m in members_rows:
                    m["declared"] = True
                    m["declared_at"] = (timezone.localtime() - datetime.timedelta(days=1)).strftime("%d-%m-%Y %H:%M")
                    m["declared_by"] = m["name"]
                    m["date"] = insp.scheduled_date.isoformat()
                insp.status = Inspection.SUBMITTED
                insp.started_at = timezone.now() - datetime.timedelta(days=2)
                insp.submitted_at = timezone.now() - datetime.timedelta(days=1)
                insp.submitted_by = users[lead]
                if scenario == "returned":
                    insp.status = Inspection.RETURNED
                    insp.return_reason = "Please complete C2 area measurements for each workshop and attach the fire safety certificate (C1.7)."
            elif scenario in ("progress", "overdue_started"):
                insp.data = full_sample_data(insp, rnd, completeness=0.45)
                insp.status = Inspection.IN_PROGRESS
                insp.started_at = timezone.now() - datetime.timedelta(days=1)
            elif scenario == "progress_low":
                insp.data = full_sample_data(insp, rnd, completeness=0.15)
                insp.status = Inspection.IN_PROGRESS
                insp.started_at = timezone.now()
            insp.progress_pct = progress(insp.data, iti.is_govt)["pct"]
            insp.save()
            if scenario in ("submitted", "progress"):
                for unit_key, label, color in (("SA.C3.1", "Sample photo: ITI name board at entrance", (60, 110, 160)),
                                               ("SA.D2.6", "Sample photo: machine test run, Fitter workshop", (90, 140, 90)),
                                               ("SA.H1.2", "Sample photo: fire point near main building", (170, 80, 60))):
                    a = Attachment(inspection=insp, unit_key=unit_key, original_name=label.split(": ")[1] + ".jpg",
                                   content_type="image/jpeg", uploaded_by=users[lead], caption=label.split(": ")[1])
                    content = _photo(label, color)
                    a.size = len(content)
                    a.file.save(f"sample_{unit_key}.jpg", ContentFile(content), save=True)
        self.stdout.write(self.style.SUCCESS(
            f"Sample data ready. Logins: {', '.join(u[0] for u in USERS)} — password: {PASSWORD}"))
