"""
ITI Inspection Proforma — digital schema.

This file is a faithful transcription of the approved proforma
("ITI Inspection Proforma", Section A – Technical Evaluation and
Section B – Institutional Office Working and Financial Matters Inspection).

Wording, numbering, norms and references are reproduced as printed, except
for the corrections approved by the Directorate (see CORRECTIONS below and
docs/CORRECTIONS.md). Do not edit item wording here without an approved
amendment to the proforma.
"""

PROFORMA_TITLE = "ITI Inspection Proforma"
PROFORMA_VERSION = "2026.1"

CPN_OPTIONS = ["C", "P", "N", "NA"]
CPN_LEGEND = "C = Complied, P = Partly complied, N = Not complied, NA = Not applicable"
YN = ["Y", "N"]
YESNO = ["Yes", "No"]

CORRECTIONS = [
    "D2: items printed as D2.10–D2.16 renumbered D2.9–D2.15 (there was no D2.9 in the printed proforma).",
    "J1 (ii) linked item 'A15' does not exist; linked to 'Any part (on-site observation)'.",
    "J1 (iii) linked item 'A14' (court cases) corrected to 'A7, A12' (time of arrival / working hours).",
    "J1 (viii) linked item 'I2.8' does not exist; linked to 'Any part (documents verified)'.",
    "J1 (ix) linked item 'I2.9' does not exist; corrected to 'I2.3'.",
    "★ legend added: ★ marks a critical item linked to a de-affiliation ground in J1.",
    "'NA' (not applicable) added as a response option to every C/P/N column, to match the NA column in J2.",
    "J2 for Part I counts I1 registers as: Maintained Y and Up to date Y = C; Maintained Y and Up to date N = P; Maintained N = N; and I2 items by their C/P/N.",
    "Section B Part F (Student Welfare Fund) is shown for Government ITIs; it is marked not applicable for other ITIs (ownership is taken from the ITI master).",
    "J8 'Signature' is recorded as an electronic declaration by each logged-in member (with date and time), plus optional upload of the signed page.",
]

STAR_LEGEND = "★ Critical item — linked to a de-affiliation ground in J1."


def _cl(sno, text, norm="", extras=None, star=False):
    row = {"sno": sno, "text": text, "norm": norm}
    if extras:
        row["extras"] = extras
    if star:
        row["star"] = True
    return row


def _num(k, label, unit=""):
    return {"k": k, "label": label, "t": "number", "unit": unit}


# ---------------------------------------------------------------------------
# SECTION A — TECHNICAL EVALUATION
# ---------------------------------------------------------------------------

PART_A = {
    "code": "A",
    "title": "Part A — General particulars",
    "blocks": [
        {
            "type": "particulars",
            "id": "A",
            "rows": [
                {"sno": "A1", "text": "Name of ITI", "fields": [{"k": "", "t": "text", "prefill": "iti_name"}]},
                {"sno": "A2", "text": "MIS code / affiliation application no.", "fields": [{"k": "", "t": "text", "prefill": "iti_mis"}]},
                {"sno": "A3", "text": "Complete address, block, district", "fields": [
                    {"k": "address", "label": "Complete address", "t": "textarea", "prefill": "iti_address"},
                    {"k": "block", "label": "Block", "t": "text", "prefill": "iti_block"},
                    {"k": "district", "label": "District", "t": "text", "prefill": "iti_district"},
                ]},
                {"sno": "A4", "text": "Located in a notified hilly area / border district (AN 9.1.3)? Yes / No",
                 "fields": [{"k": "", "t": "radio", "options": YESNO}]},
                {"sno": "A5", "text": "Principal: name, mobile, e-mail", "fields": [
                    {"k": "name", "label": "Name", "t": "text", "prefill": "principal_name"},
                    {"k": "mobile", "label": "Mobile", "t": "tel", "prefill": "principal_mobile"},
                    {"k": "email", "label": "E-mail", "t": "email", "prefill": "principal_email"},
                ]},
                {"sno": "A6", "text": "Type of inspection: Periodic / Surprise / Renewal (AN 3.6) / Complaint-based (AN 7.3.2) / Other",
                 "fields": [
                     {"k": "", "t": "radio", "options": ["Periodic", "Surprise", "Renewal (AN 3.6)", "Complaint-based (AN 7.3.2)", "Other"]},
                     {"k": "other", "label": "If Other, specify", "t": "text"},
                 ]},
                {"sno": "A7", "text": "Date of inspection; time of arrival and departure", "fields": [
                    {"k": "date", "label": "Date of inspection", "t": "date"},
                    {"k": "arrival", "label": "Time of arrival", "t": "time"},
                    {"k": "departure", "label": "Time of departure", "t": "time"},
                ]},
                {"sno": "A8", "text": "Geo-coordinates at inspection site (latitude, longitude)", "fields": [
                    {"k": "lat", "label": "Latitude", "t": "lat"},
                    {"k": "lng", "label": "Longitude", "t": "lng"},
                ], "geo": True},
                {"sno": "A9", "text": "Inspecting team: name, designation, office of each member", "fields": [
                    {"k": "", "t": "rows", "prefill": "team", "columns": [
                        {"k": "name", "label": "Name", "t": "text"},
                        {"k": "designation", "label": "Designation", "t": "text"},
                        {"k": "office", "label": "Office", "t": "text"},
                    ]},
                ]},
                {"sno": "A10", "text": "Date of last inspection, by whom (State / RDSDE / DGT)", "fields": [
                    {"k": "date", "label": "Date of last inspection", "t": "date"},
                    {"k": "by", "label": "By whom", "t": "radio", "options": ["State", "RDSDE", "DGT"]},
                ]},
                {"sno": "A11", "text": "Action taken on observations of the last inspection: complied / partly / not complied (TM 2.21(v))",
                 "fields": [{"k": "", "t": "radio", "options": ["complied", "partly", "not complied"]}]},
                {"sno": "A12", "text": "Normal working hours and shifts in operation (TM 2.10: 7½ h/day, 40 h/week)", "fields": [
                    {"k": "hours", "label": "Normal working hours", "t": "text"},
                    {"k": "shifts", "label": "Shifts in operation", "t": "text"},
                ]},
                {"sno": "A13", "text": "Latest DGT grading score / grade of the ITI", "fields": [
                    {"k": "score", "label": "Score", "t": "text"},
                    {"k": "grade", "label": "Grade", "t": "text"},
                ]},
                {"sno": "A14", "text": "Court cases pending, if any: court, case no., issue, status (TM Part II)", "fields": [
                    {"k": "", "t": "rows", "columns": [
                        {"k": "court", "label": "Court", "t": "text"},
                        {"k": "case_no", "label": "Case no.", "t": "text"},
                        {"k": "issue", "label": "Issue", "t": "text"},
                        {"k": "status", "label": "Status", "t": "text"},
                    ]},
                ]},
            ],
        }
    ],
}

PART_B = {
    "code": "B",
    "title": "Part B — Affiliation status, trades and units",
    "blocks": [
        {
            "type": "grid", "id": "B1",
            "title": "B1. Trade-wise position (one row per trade; add rows as needed)",
            "columns": [
                {"k": "trade", "label": "Trade", "t": "text"},
                {"k": "ncvet_scvt", "label": "NCVET / SCVT", "t": "select", "options": ["NCVET", "SCVT"]},
                {"k": "duration", "label": "Duration", "t": "text"},
                {"k": "units_s1", "label": "Units affiliated (Shift 1 / 2 / 3) — Shift 1", "short": "Units affl. S1", "t": "number"},
                {"k": "units_s2", "label": "Units affiliated (Shift 1 / 2 / 3) — Shift 2", "short": "S2", "t": "number"},
                {"k": "units_s3", "label": "Units affiliated (Shift 1 / 2 / 3) — Shift 3", "short": "S3", "t": "number"},
                {"k": "order", "label": "Affiliation order no. & date", "t": "text"},
                {"k": "seats", "label": "Seats per unit", "t": "number"},
                {"k": "enr_1", "label": "Enrolled: 1st yr / 2nd yr — 1st yr", "short": "Enrolled 1st yr", "t": "number"},
                {"k": "enr_2", "label": "Enrolled: 1st yr / 2nd yr — 2nd yr", "short": "2nd yr", "t": "number"},
                {"k": "running", "label": "Units actually running", "t": "number"},
                {"k": "remarks", "label": "Remarks", "t": "text"},
            ],
            "min_rows": 1,
        },
        {
            "type": "checklist", "id": "B2", "title": "B2. Compliance checks",
            "rows": [
                _cl("B2.1", "Affiliation valid on date of inspection", "Initial affiliation is for 6 years (AN 3.6)"),
                _cl("B2.2", "Renewal applied on portal at least 1 year before expiry",
                    "AN 3.6(i); late filing bars new admissions after 6 years (AN 3.6(ix))"),
                _cl("B2.3", "No trade or unit run without affiliation; admissions within affiliated seats", "AN 7.2(x), (xi)"),
                _cl("B2.4", "Institute running at the approved location only",
                    "Shifting without DGT / State approval is a ground for de-affiliation (AN 7.2(vii), AN 3.2)"),
                _cl("B2.5", "Name of ITI matches affiliation order; any change approved", "AN 3.3"),
                _cl("B2.6", "Trade details board displays affiliated trades, seating capacity and number enrolled",
                    "AN 9.2, Table 24 item 4.4"),
                _cl("B2.7", "Affiliation status of each trade (NCVET / SCVT) made known to applicants before admission",
                    "TM Part II 1.5(ii)"),
                _cl("B2.8", "Data on the affiliation / MIS/SIDH portal (trades, units, trainees, staff) matches the ground position",
                    "AN 2.5.4.1, AN 3.6(ii)"),
            ],
        },
    ],
}

PART_C = {
    "code": "C",
    "title": "Part C — Land, building and infrastructure",
    "blocks": [
        {
            "type": "checklist", "id": "C1", "title": "C1. Land and building documents",
            "rows": [
                _cl("C1.1", "Land owned (registered deed) or on a registered lease in the institute’s name, valid for at least 6 years",
                    "AN 9.1.5; operating without a live lease is a de-affiliation ground (AN 7.2(v))"),
                _cl("C1.2", "Land area against norm",
                    "General areas: 3,000 / 2,115 / 1,821 sq m for 4 trades (single / double / 3+ storey), AN Table 21. "
                    "Hilly areas, NE, border districts: 1,200 sq m for 2 trades with 1+1 units, AN Table 23"),
                _cl("C1.3", "Single contiguous plot with boundary wall; split levels allowed in hilly areas",
                    "AN 9.1.4(iii), 9.1.5(iii), 9.1.6(iii)"),
                _cl("C1.4", "Land-use conversion certificate (if agricultural land)", "AN Ann-15, item 10"),
                _cl("C1.5", "Building plan approved by competent authority; actual construction matches plan",
                    "AN 9.2.3, Table 26; AN Ann-15, item 11"),
                _cl("C1.6", "Building Completion Certificate (new ITI) or Structural Safety Certificate (existing ITI) in prescribed format, naming the ITI",
                    "AN Table 26; formats at AN Ann-10 / Ann-11. Govt ITIs may give the handing-over certificate of the construction agency"),
                _cl("C1.7", "Fire Safety Certificate from State Fire Department, valid and address matching", "AN Table 26 item 3; AN 10.1"),
                _cl("C1.8", "No classroom, workshop, IT lab, office or amenity in basement / cellar", "AN 9.2.4(iv)"),
                _cl("C1.9", "Lift provided and maintained if more than 3 floors", "AN 9.1.6(iv), 9.2.4(viii)–(ix)"),
                _cl("C1.10", "Heavy-machinery trades (Fitter, Turner, Machinist, Welder, Mech. Diesel / MV / Tractor, Sheet Metal, Foundry, Tool & Die, Mason, any machine over 200 kg) on ground floor",
                    "AN 9.1.6(vi)"),
                _cl("C1.11", "Ramps, rails and PwD toilets provided", "AN 9.1.6(v), 9.2.4(vi), 10.5"),
                _cl("C1.12", "Internal walls plastered and painted; cement or tiled floors; doors and windows painted", "AN 9.2.2"),
                _cl("C1.13", "Approach/ Motor able Road to the Institute available", ""),
            ],
        },
        {
            "type": "area", "id": "C2",
            "title": "C2. Area verification (measure on site; workshop area per trade is as per AN Ann-19 / current curriculum)",
            "rows": [
                {"sno": "C2.1", "text": "Workshop — each trade and unit (add rows)", "repeat": True,
                 "norm": "Area per Ann-19; rectangular, min. width 5 m; RCC or profiled industrial roof sheets; no tin / asbestos roof or tin walls; separate workshop for each unit (AN Table 24, 1.2)"},
                {"sno": "C2.2", "text": "Classroom — each trade and unit (add rows)", "repeat": True,
                 "norm": "25 sq m, min. width 3 m; tiled floor; RCC roof; one chair / desk per trainee (AN Table 24, 1.1)"},
                {"sno": "C2.3", "text": "IT lab",
                 "norm": "25 sq m for 10 PCs (up to 100 trainees per shift) + 2.5 sq m per extra PC; width 3 m; tiled. Not needed if only COPA is run (AN Table 24, 1.3)"},
                {"sno": "C2.4", "text": "Multipurpose / drawing hall",
                 "norm": "110 sq m, width 5 m, for up to 160 trainees per shift; proportionate beyond (AN Table 24, 1.4)"},
                {"sno": "C2.5", "text": "Raw material store; separate oil and gas store",
                 "norm": "90 sq m (engineering), 30 sq m (non-engineering) (AN Table 24, 1.5)"},
                {"sno": "C2.6", "text": "Principal's room", "norm": "20 sq m"},
                {"sno": "C2.7", "text": "Reception-cum-waiting lobby", "norm": "40 sq m"},
                {"sno": "C2.8", "text": "Staff room", "norm": "20 sq m"},
                {"sno": "C2.9", "text": "Placement / counselling room", "norm": "50 sq m"},
                {"sno": "C2.10", "text": "Administrative hall / section", "norm": "20 sq m"},
                {"sno": "C2.11", "text": "Library and reading room", "norm": "40 sq m for up to 160 trainees per shift"},
                {"sno": "C2.12", "text": "First-aid room", "norm": "15 sq m (no fixed minimum in hilly areas, AN 9.1.4(v))"},
                {"sno": "C2.13", "text": "Playground", "norm": "As per building bye-laws / NBC"},
                {"sno": "C2.14", "text": "Toilets", "norm": "Separate for staff, boys, girls and PwD"},
                {"sno": "C2.15", "text": "Treated drinking water", "norm": "On every floor and in workshops"},
                {"sno": "C2.16", "text": "Parking", "norm": "General parking separate from trade parking (e.g. Mech. Diesel)"},
            ],
            "footnote": "Area norms C2.6–C2.16 are from AN Table 24, sections 2–3.",
        },
        {
            "type": "checklist", "id": "C3", "title": "C3. Signage (AN Table 24, section 4)",
            "rows": [
                _cl("C3.1", "Board at plot entrance and on building: bilingual, font at least 75 mm, ITI name, MIS code, address, ITI / Skill India / DGT logos",
                    "Items 4.1–4.2"),
                _cl("C3.2", "Directional boards (workshops, office, hostel, scrap yard)", "Item 4.3"),
                _cl("C3.3", "Staff details board (name, qualification, contact of Principal and instructors)", "Item 4.5"),
                _cl("C3.4", "Exit signs, danger signs near transformer / DG set / panels, prohibited-area signs near running machinery",
                    "Items 4.6–4.8"),
                _cl("C3.5", "Sexual Harassment Redressal Committee notice displayed", "Item 4.9"),
                _cl("C3.6", "Whether schemes related to the trainee’s welfare being showcased in the notice board and properly sensitized through digital mode such as ATS, PM Internship Scheme, National Scholarship portal, Skill development allowance scheme etc.",
                    ""),
            ],
        },
        {
            "type": "checklist", "id": "C4", "title": "C4. Electricity, IT lab and other mandatory requirements",
            "rows": [
                _cl("C4.1", "3-phase commercial connection in the name of institute (or managing body, with resolution per Ann-6)",
                    "AN 9.3(i)–(iii)"),
                _cl("C4.2", "Sanctioned load (kW) not less than required load",
                    "Required load = Σ (standard load per unit × base units) for all trades (AN 9.3(v)). Sanctioned: ___ kW; required: ___ kW",
                    extras=[_num("sanctioned_kw", "Sanctioned", "kW"), _num("required_kw", "Required", "kW")]),
                _cl("C4.3", "Backup power (DG set or solar with battery), installed and maintained", "AN 9.3(vi)–(viii)"),
                _cl("C4.4", "Desktop computers, latest configuration, in working order",
                    "10 for up to 100 trainees per shift + 2 per extra 20 trainees (AN Table 25). Required: ___; working: ___",
                    extras=[_num("required", "Required"), _num("working", "Working")]),
                _cl("C4.5", "Internet connection", "Minimum 40 Mbps or high-speed Wi-Fi (AN Table 25)"),
                _cl("C4.6", "Licensed OS, antivirus, multimedia, UPS; LAN, laser printer, scanner, 1 TB external HDD; 20 chairs, 10 tables, white board",
                    "AN Table 25"),
                _cl("C4.7", "Separate biometric machines with GPS for staff and for trainees, installed and in use",
                    "AN 9.4(i); AN Ann-15, item 27"),
                _cl("C4.8", "Projector for e-learning", "AN 9.4(ii)"),
                _cl("C4.9", "Disaster Management Plan prepared and available", "AN 9.4(iii)"),
            ],
        },
    ],
}

PART_D = {
    "code": "D",
    "title": "Part D — Workshops, machinery, tools and equipment",
    "blocks": [
        {
            "type": "grid", "id": "D1",
            "title": "D1. Trade-wise equipment position (check against the DGT tools and equipment list in the current curriculum; one row per trade and unit)",
            "columns": [
                {"k": "trade_unit", "label": "Trade / unit", "t": "text"},
                {"k": "dgt_items", "label": "Items in DGT list (W + T)", "t": "number"},
                {"k": "available", "label": "Available", "t": "number"},
                {"k": "installed", "label": "Installed and grouted", "t": "number"},
                {"k": "working", "label": "In working order", "t": "number"},
                {"k": "shortfall", "label": "Shortfall: list S.Nos", "t": "text"},
                {"k": "obsolete", "label": "Obsolete / to be replaced", "t": "text"},
                {"k": "remarks", "label": "Remarks", "t": "text"},
            ],
            "min_rows": 1,
        },
        {
            "type": "checklist", "id": "D2", "title": "D2. Compliance checks",
            "rows": [
                _cl("D2.1", "Machinery and equipment available as per curriculum for every affiliated trade and unit", "AN 7.2(i); AN Ann-15, item 25"),
                _cl("D2.2", "Purchase invoices in the name of the institute and complete", "AN Ann-15, item 25"),
                _cl("D2.3", "Shop-floor machines grouted to foundation", "AN Ann-12(1)"),
                _cl("D2.4", "Items costing Rs 10,000 or more hard-punched / engraved with ITI name and MIS code", "AN Ann-12(2)"),
                _cl("D2.5", "All items carry identification stickers in DGT-list sequence (W1…Wn, T1…Tn; unit suffix /1, /2; separate colours per trade)",
                    "AN Ann-12(2)(b)–(g)"),
                _cl("D2.6", "Machines run during inspection (sample-test at least 3 per trade)", "AN Ann-14(4); AN Ann-15, item 25"),
                _cl("D2.7", "Machines used to full capacity; idle machines listed with reason", "TM App-XV, Proforma item 4(iii)"),
                _cl("D2.8", "Maintenance system followed; machine history cards / maintenance log kept", "TM App-XV, Proforma item 4(v)"),
                # Printed as D2.10 onwards; renumbered (approved correction).
                _cl("D2.9", "Raw material adequate for practical exercises; expenditure per trainee per month recorded: Rs ___",
                    "TM App-XV items 26, Proforma 5(vi); TM 2.14(1)",
                    extras=[_num("rs_per_trainee", "Expenditure per trainee per month", "Rs")]),
                _cl("D2.10", "Stores: adequate space, layout, receipt and issue system; result of test check of stock registers against physical stock",
                    "TM App-XV item 16"),
                _cl("D2.11", "Section layout plan showing machine positions, specifications and connected load displayed in each workshop",
                    "TM 2.20(ii)(a)"),
                _cl("D2.12", "Syllabus, standard tools and equipment list, and week-wise syllabus break-up displayed in workshop",
                    "TM 2.20(ii)(b)–(c)"),
                _cl("D2.13", "Safety precautions affixed on each machine; SOP displayed near machines", "AN 10.4(iv)–(v)"),
                _cl("D2.14", "Instructions on maintenance of machines displayed", "TM 2.20(ii)(g)"),
                _cl("D2.15", "Packing and instruction booklets removed; machines in use, not stored", "AN Ann-12(2)(a)"),
            ],
        },
        {
            "type": "grid", "id": "DTC",
            "title": "Test-check record: list any machines found missing, not installed or not working, by trade and DGT-list S.No.",
            "columns": [
                {"k": "trade_unit", "label": "Trade / unit", "t": "text"},
                {"k": "dgt_sno", "label": "DGT-list S.No", "t": "text"},
                {"k": "item", "label": "Item", "t": "text"},
                {"k": "found", "label": "Found: missing / not installed / not working", "t": "select",
                 "options": ["missing", "not installed", "not working"]},
                {"k": "remarks", "label": "Remarks", "t": "text"},
            ],
            "min_rows": 1,
        },
    ],
}

E1_POSTS = [
    ("principal", "Principal", "1 per ITI (Jr. scale up to 399 seats; Sr. scale 400+)"),
    ("vice_principal", "Vice-Principal", "1 per additional 300 seats above 400"),
    ("group_instructor", "Group Instructor", "1 per 8 units"),
    ("trade_instructors", "Trade instructors (trade-wise; add rows)", "As per curriculum for each unit; TM: 2 for two units, one with diploma / degree"),
    ("wcs_ed", "Workshop Calculation & Science / Engineering Drawing instructor", "1 per 144 engineering seats (TM); as per curriculum"),
    ("es", "Employability Skills instructor", "Full-time for 1,000+ seats; otherwise contract / outsourced"),
    ("tpo", "Training & Placement Officer / industry liaison", "Post for 1,000+ seats; designated staff member otherwise"),
    ("storekeeper", "Storekeeper", "1 up to 250 seats; more for larger ITIs"),
    ("accountant", "Accountant", "1 per ITI"),
    ("librarian", "Librarian", "1 for 400+ seats (recommended)"),
    ("clerical", "Clerical and workshop attendants", "As per TM 3.2 table / State norms"),
]

PART_E = {
    "code": "E",
    "title": "Part E — Principal, instructors and staff",
    "blocks": [
        {
            "type": "staffing", "id": "E1",
            "title": "E1. Staffing position (norms from TM 3.2; instructor-to-unit ratio and qualification as per current CTS curriculum)",
            "columns": [
                {"k": "sanctioned", "label": "Sanctioned / required", "t": "number"},
                {"k": "in_position", "label": "In position", "t": "number"},
                {"k": "vacant", "label": "Vacant", "t": "number"},
                {"k": "remarks", "label": "Remarks", "t": "text"},
            ],
            "posts": [{"k": k, "post": p, "norm": n} for k, p, n in E1_POSTS],
            "trade_rows_after": "trade_instructors",
        },
        {
            "type": "grid", "id": "E2",
            "title": "E2. Individual verification (Principal and every instructor; verify originals)",
            "columns": [
                {"k": "name", "label": "Name", "t": "text"},
                {"k": "post", "label": "Post / trade / unit", "t": "text"},
                {"k": "qualification", "label": "Qualification", "t": "text"},
                {"k": "cits", "label": "CITS / CTI trained (Y/N)", "t": "select", "options": YN},
                {"k": "experience", "label": "Experience (years)", "t": "number"},
                {"k": "regular", "label": "Regular / contract", "t": "select", "options": ["Regular", "Contract"]},
                {"k": "doj", "label": "Date of joining", "t": "date"},
                {"k": "salary_bank", "label": "Salary paid through bank, last 6 months (Y/N)", "t": "select", "options": YN},
                {"k": "present", "label": "Present today (Y/N)", "t": "select", "options": YN},
                {"k": "meets", "label": "Meets norms (Y/N)", "t": "select", "options": YN},
            ],
            "fixed_first": {"post": "Principal"},
            "min_rows": 1,
        },
        {
            "type": "checklist", "id": "E3", "title": "E3. Compliance checks",
            "rows": [
                _cl("E3.1", "Required number of instructors available for every affiliated trade and unit", "AN 7.2(iv)"),
                _cl("E3.2", "Staff attendance by Him Upasthithi App; matches head-count on the day", "AN 9.4(i)"),
                _cl("E3.3", "Weekly duty timetable for each instructor and supervisor, spare time used for checking work, progress cards, registers, visual aids and maintenance",
                    "TM 2.11(1), 2.18"),
                _cl("E3.4", "Instructors trained in instruction methods (CITS / CSTARI / NSTI); plan for untrained staff", "TM App-XV item 14"),
                _cl("E3.5", "Industry deputation / refresher training of instructors; staff training plan from self-appraisal", "TM 2.28, 2.29"),
                _cl("E3.6", "General standard and subject knowledge of instructors: inspector's assessment from class observation",
                    "TM 2.25(vi)(c), App-XV item 13"),
            ],
        },
    ],
}

PART_F = {
    "code": "F",
    "title": "Part F — Admissions and training delivery",
    "blocks": [
        {
            "type": "grid", "id": "F1",
            "title": "F1. Trainee strength, last three sessions (TM App-XV item 6)",
            "header_inputs": [
                {"k": "s1", "label": "Session ___ (1)", "t": "text"},
                {"k": "s2", "label": "Session ___ (2)", "t": "text"},
                {"k": "s3", "label": "Session ___ (3)", "t": "text"},
            ],
            "columns": [
                {"k": "trade", "label": "Trade", "t": "text"},
                {"k": "s1_adm", "label": "Session (1): admitted", "group": "s1", "t": "number"},
                {"k": "s1_drop", "label": "Session (1): dropped out", "group": "s1", "t": "number"},
                {"k": "s1_pass", "label": "Session (1): passed", "group": "s1", "t": "number"},
                {"k": "s2_adm", "label": "Session (2): admitted", "group": "s2", "t": "number"},
                {"k": "s2_drop", "label": "Session (2): dropped out", "group": "s2", "t": "number"},
                {"k": "s2_pass", "label": "Session (2): passed", "group": "s2", "t": "number"},
                {"k": "s3_adm", "label": "Session (3): admitted", "group": "s3", "t": "number"},
                {"k": "s3_drop", "label": "Session (3): dropped out", "group": "s3", "t": "number"},
                {"k": "s3_pass", "label": "Session (3): passed", "group": "s3", "t": "number"},
                {"k": "women", "label": "Women", "t": "number"},
                {"k": "pwd", "label": "PwD", "t": "number"},
            ],
            "min_rows": 1,
        },
        {
            "type": "grid", "id": "F2",
            "title": "F2. Head-count on the day of inspection",
            "columns": [
                {"k": "trade_unit_year", "label": "Trade / unit / year", "t": "text"},
                {"k": "on_rolls", "label": "On rolls", "t": "number"},
                {"k": "marked", "label": "Marked present (biometric)", "t": "number"},
                {"k": "physical", "label": "Physically present", "t": "number"},
                {"k": "difference", "label": "Difference", "t": "number"},
                {"k": "remarks", "label": "Remarks", "t": "text"},
            ],
            "min_rows": 1,
        },
        {
            "type": "checklist", "id": "F3", "title": "F3. Admissions and fees",
            "rows": [
                _cl("F3.1", "Admission purely on merit of qualifying exam marks (or Directorate's written test)", "TM 2.9(4); TM Part II 1.6(i)(b)"),
                _cl("F3.2", "Minimum age 14 years; entry qualification as per trade syllabus", "TM 2.9(1)–(2)"),
                _cl("F3.3", "Reservation for SC / ST / OBC, women (30% horizontal) and PwD followed as per current State and Central policy", "TM 2.9(3)"),
                _cl("F3.4", "Admissions within seats affiliated; completed by the cut-off date", "TM 2.9(4)"),
                _cl("F3.5", "Original certificates of trainees kept in safe custody; receipts given", "TM Part II 1.6(i)(c)"),
                _cl("F3.6", "Prospectus / brochure giving rules, attendance norms, fees and assessment criteria", "TM Part II 1.6 (COE guidelines (b))"),
                _cl("F3.7", "Fees charged not more than the fee prescribed by DGT / State; receipts issued for all collections", "AN 7.2(vi)", star=True),
                _cl("F3.8", "Stipend / scholarship disbursed to eligible trainees in time, through bank", "TM 2.10(5); TM App-XV item 4"),
                _cl("F3.9", "Students insured in Time or not", ""),
            ],
        },
        {
            "type": "checklist", "id": "F4", "title": "F4. Training delivery",
            "rows": [
                _cl("F4.1", "Latest curriculum available with every instructor", "TM App-XV, Proforma 5(i)"),
                _cl("F4.2", "Syllabus broken up into weekly / monthly schedule; lesson plans and demonstration plans prepared", "TM App-XV, Proforma 5(ii); TM 2.20(ii)(c)"),
                _cl("F4.3", "Weekly timetable for each section displayed and followed; total instructional hours as per curriculum (TM: 42 h / week)", "TM 2.10(1), 2.18"),
                _cl("F4.4", "Practical exercises designed to cover the full syllabus; section progress chart shows exercises completed by each trainee", "TM App-XV 5(v); TM 2.20(ii)(e)"),
                _cl("F4.5", "Progress card kept for every trainee from admission; monthly tests held and recorded", "TM 2.11(4); TM App-VIII"),
                _cl("F4.6", "Audio-visual aids, charts, models and e-learning (projector) used", "TM App-XV 5(iii); AN 9.4(ii)"),
                _cl("F4.7", "Weekly model lesson / demonstration class for instructors, with record", "TM 2.11(2)"),
                _cl("F4.8", "Industrial visits, OJT / training in industry arranged; record kept", "TM 2.11(3); TM Part II 1.9"),
                _cl("F4.9", "Remedial measures for trainees weak in skills", "TM App-XV 5(xii)"),
                _cl("F4.10", "Monthly staff meeting held with minutes and action taken (ITIs over 250 seats)", "TM 2.19"),
                _cl("F4.11", "Internal inspection of sections by Principal / Group Instructor recorded, with follow-up", "TM 2.21"),
                _cl("F4.12", "Reference material in Principal's office: layout plans (institute, workshops, electrical), organisation chart, duty charts, trade-wise pass-out chart", "TM 2.20(i)"),
                _cl("F4.13", "Learning environment: illumination, ventilation, cleanliness, protection from dust, heat, cold and rain, noise control", "TM Part II 1.7"),
            ],
        },
        {
            "type": "checklist", "id": "F5", "title": "F5. Attendance and discipline",
            "rows": [
                _cl("F5.1", "Trainee attendance marked by biometric (existing ITIs) and matches head-count (F2)", "AN Ann-15, item 27"),
                _cl("F5.2", "Attendance register maintained; eligibility for final exam based on 80% attendance", "TM 2.10(2)"),
                _cl("F5.3", "Absent 10 consecutive days without leave struck off as absconder; warnings issued for unauthorised absence", "TM 2.10(4)(v)–(vi)"),
                _cl("F5.4", "Leave records (casual, medical, special) kept within prescribed limits", "TM 2.10(4)"),
                _cl("F5.5", "General discipline and punctuality; trainees in uniform / overalls", "TM App-XV item 11; TM 2.10(7)"),
            ],
        },
        {
            "type": "grid", "id": "FCO",
            "title": "Class observation notes (one theory and one practical class): trade, instructor, topic, quality of delivery, trainee engagement, skill test-check result.",
            "columns": [
                {"k": "trade_unit", "label": "Trade / unit", "t": "text"},
                {"k": "instructor", "label": "Instructor", "t": "text"},
                {"k": "kind", "label": "Theory / practical", "t": "select", "options": ["Theory", "Practical"]},
                {"k": "topic", "label": "Topic or exercise", "t": "text"},
                {"k": "observation", "label": "Observation", "t": "textarea"},
                {"k": "result", "label": "Test-check result", "t": "text"},
            ],
            "initial_rows": [{"kind": "Theory"}, {"kind": "Practical"}],
            "min_rows": 2,
        },
    ],
}

PART_G = {
    "code": "G",
    "title": "Part G — Assessment, examinations and certification",
    "blocks": [
        {
            "type": "grid", "id": "G1",
            "title": "G1. Results of All India Trade Test, last three years",
            "header_inputs": [
                {"k": "y1", "label": "Year ___ (1)", "t": "text"},
                {"k": "y2", "label": "Year ___ (2)", "t": "text"},
                {"k": "y3", "label": "Year ___ (3)", "t": "text"},
            ],
            "columns": [
                {"k": "trade", "label": "Trade", "t": "text"},
                {"k": "y1_app", "label": "Year (1): appeared", "group": "y1", "t": "number"},
                {"k": "y1_pass", "label": "Year (1): passed", "group": "y1", "t": "number"},
                {"k": "y1_pct", "label": "Year (1): pass %", "group": "y1", "t": "number", "calc": ["pct", "y1_pass", "y1_app"]},
                {"k": "y2_app", "label": "Year (2): appeared", "group": "y2", "t": "number"},
                {"k": "y2_pass", "label": "Year (2): passed", "group": "y2", "t": "number"},
                {"k": "y2_pct", "label": "Year (2): pass %", "group": "y2", "t": "number", "calc": ["pct", "y2_pass", "y2_app"]},
                {"k": "y3_app", "label": "Year (3): appeared", "group": "y3", "t": "number"},
                {"k": "y3_pass", "label": "Year (3): passed", "group": "y3", "t": "number"},
                {"k": "y3_pct", "label": "Year (3): pass %", "group": "y3", "t": "number", "calc": ["pct", "y3_pass", "y3_app"]},
                {"k": "remarks", "label": "Remarks", "t": "text"},
            ],
            "min_rows": 1,
        },
        {
            "type": "checklist", "id": "G2", "title": "G2. Compliance checks",
            "rows": [
                _cl("G2.1", "Only trainees of affiliated trades / units sent for AITT", "TM Part II 1.5(ii)"),
                _cl("G2.2", "Exam eligibility list prepared on 80% attendance rule; condonation cases recorded with reasons", "TM 2.10(2)"),
                _cl("G2.3", "Continuous assessment: monthly / quarterly tests, sessional marks recorded", "TM Part II 1.5(vi); TM 2.11(4)"),
                _cl("G2.4", "Periodic evaluation of trainee progress and system followed", "TM App-XV, Proforma 5(vii)"),
                _cl("G2.5", "Duplicate certificate and re-totalling requests handled as prescribed", "TM 4.55, 4.56"),
                _cl("G2.6", "Trainees encouraged to take part in skill competitions, Outcome of Competition.", "TM 4.57"),
            ],
        },
    ],
}

PART_H = {
    "code": "H",
    "title": "Part H — Safety, amenities and trainee welfare",
    "blocks": [
        {"type": "note", "text": "All items in H1–H6 are essential requirements under AN Chapter 10 unless marked (D) for desirable. In Himachal Pradesh, the earthquake and landslide items in H6 apply to every ITI."},
        {
            "type": "checklist", "id": "H1", "title": "H1. Fire safety (AN 10.1, 10.7)", "no_norm": True,
            "rows": [
                _cl("H1.1", "Fire safety certificate from local fire authority (see C1.7)"),
                _cl("H1.2", "Fire point in front of each building: 2 water buckets, 2 sand buckets, 4 extinguishers (one of each type)"),
                _cl("H1.3", "At least 2 extinguishers at each prominent location; refill / expiry dates current"),
                _cl("H1.4", "Sand buckets on stands near workshops, labs, DG room, transformer, sub-station"),
                _cl("H1.5", "Every exit and exit route kept free of obstruction; retroreflective escape signage"),
                _cl("H1.6", "Fire drills held; evacuation drill every quarter for each building, with record"),
                _cl("H1.7", "Standing Fire Order maintained; assembly point designated"),
                _cl("H1.8", "Standard fire safety norms with emergency numbers displayed on every floor"),
                _cl("H1.9", "(D) CCTV covering fire safety systems"),
            ],
        },
        {
            "type": "checklist", "id": "H2", "title": "H2. Electrical safety (AN 10.2)", "no_norm": True,
            "rows": [
                _cl("H2.1", "Proper earthing and bonding of wiring; major equipment earthed separately"),
                _cl("H2.2", "Rubber / insulating mats in front of every electric panel"),
                _cl("H2.3", "ELCBs installed where required"),
                _cl("H2.4", "No overhead high-tension line across premises"),
                _cl("H2.5", "Neutral of each generator and transformer earthed by two separate connections"),
                _cl("H2.6", "Transformer / sub-station segregated, with CO2, DCP, foam extinguishers and sand buckets nearby"),
                _cl("H2.7", "Transformers and switchgear maintained on BIS-based schedule; work done only by licensed electricians"),
                _cl("H2.8", "(D) Lightning arrester on buildings; 1 m clear space in front of switchboards; periodic insulation and load tests"),
            ],
        },
        {
            "type": "checklist", "id": "H3", "title": "H3. Workshop safety (AN 10.4)", "no_norm": True,
            "rows": [
                _cl("H3.1", "PPE provided to everyone entering the workshop, and in use"),
                _cl("H3.2", "Safety instructions and Do's and Don'ts displayed inside and outside each workshop"),
                _cl("H3.3", "First-aid kit maintained in each workshop"),
                _cl("H3.4", "Emergency contact numbers displayed (safety officer, fire, medical, security, maintenance)"),
                _cl("H3.5", "All electrically operated machines earthed and bonded"),
                _cl("H3.6", "(D) Aisles and gangways marked; non-skid floor; housekeeping schedule; fuel stored in minimum quantity; ventilation; fume extraction for welding trades"),
            ],
        },
        {
            "type": "checklist", "id": "H4", "title": "H4. Drinking water and food (AN 10.3)", "no_norm": True,
            "rows": [
                _cl("H4.1", "Tanks and pipelines cleaned and disinfected periodically; cleaning log kept"),
                _cl("H4.2", "Water tested at a Government-certified lab at least once in 3 months (IS 10500); last report dated ___",
                    extras=[{"k": "last_report", "label": "Last report dated", "t": "date"}]),
                _cl("H4.3", "Potable water points with RO / UV filtration, maintained"),
                _cl("H4.4", "Hand-washing stations near canteen and eating areas"),
                _cl("H4.5", "(D) Canteen food samples lab-tested every 6 months"),
            ],
        },
        {
            "type": "checklist", "id": "H5", "title": "H5. Persons with disabilities (AN 10.5)", "no_norm": True,
            "rows": [
                _cl("H5.1", "Ramp for access and evacuation"),
                _cl("H5.2", "Wheelchairs and stretchers available"),
            ],
        },
        {
            "type": "checklist", "id": "H6", "title": "H6. Emergency and disaster preparedness (AN 10.6)", "no_norm": True,
            "rows": [
                _cl("H6.1", "Emergency evacuation plan; outside cut-offs for water, electricity and LPG"),
                _cl("H6.2", "Periodic structural audit of buildings"),
                _cl("H6.3", "Public address system; power backup for exit lighting; trained student volunteers"),
                _cl("H6.4", "Earthquake: quarterly exit drills with records; trained evacuation team; heavy items placed low; light fittings braced; glass panes protected"),
                _cl("H6.5", "Landslide: retaining walls where erosion-prone; staff trained to recognise early signs"),
            ],
        },
        {
            "type": "checklist", "id": "H7", "title": "H7. Amenities and welfare",
            "rows": [
                _cl("H7.1", "First-aid facility; tie-up with doctor / clinic / hospital", "TM 3.2 (medical staff); AN Table 24, 3.2"),
                _cl("H7.2", "Toilets clean and functional, separate for staff, boys, girls, PwD", "AN Table 24, 3.6"),
                _cl("H7.3", "Canteen and basic amenities available", "AN 9.1.4(v)"),
                _cl("H7.4", "Library: condition, books, technical magazines, syllabi, question papers, instructional media; use by staff and trainees", "TM App-XV item 17"),
                _cl("H7.5", "Sports and recreation facilities; funds available", "TM App-XV item 18(iii); TM 2.14(6)"),
                _cl("H7.6", "Hostel (if any): rooms, sanitation, mess, warden, extra-curricular facilities", "TM App-XV item 19"),
                _cl("H7.7", "Internal Committee against sexual harassment constituted and displayed", "AN Table 24, 4.9"),
                _cl("H7.8", "Complaint handling procedure; complaint register with action taken", "TM Part II 2.3"),
                _cl("H7.9", "Placement cell; placement records including self-employment", "TM Part II 1.10(ii)–(iv)"),
                _cl("H7.10", "Follow-up record cards of passed-out trainees", "TM 2.15; TM App-X"),
                _cl("H7.11", "Special facilities for SC / ST, women and PwD trainees", "TM App-XV items 21–22"),
                _cl("H7.12", "(D) Sanitary napkin vending machine if more than 50 women trainees; sanitary waste disposal", "AN 9.5(ii)"),
                _cl("H7.13", "(D) Rainwater harvesting, solar power, waste segregation, CCTV, announcement system, ERP", "AN 9.5"),
                _cl("H7.14", "Morning Assembly area availability", ""),
            ],
        },
    ],
}

PART_I = {
    "code": "I",
    "title": "Part I — Records, registers, finance and governance",
    "blocks": [
        {
            "type": "register", "id": "I1",
            "title": "I1. Registers and records (inspect the original; test-check entries against physical position)",
            "rows": [
                {"sno": "I1.1", "text": "Admission register and trainee personal files", "norm": "TM 2.9; TM Part II 1.6"},
                {"sno": "I1.2", "text": "Trainee attendance: biometric report and register", "norm": "TM 2.10(2); AN 9.4"},
                {"sno": "I1.3", "text": "Staff attendance and movement register", "norm": "AN 9.4"},
                {"sno": "I1.4", "text": "Progress cards and sectional registers", "norm": "TM 2.11(4), 2.18"},
                {"sno": "I1.5", "text": "Stock registers: consumable, non-consumable, dead stock; annual physical verification", "norm": "TM App-XV item 16"},
                {"sno": "I1.6", "text": "Raw material issue register (trade-wise)", "norm": "TM App-XV item 26"},
                {"sno": "I1.7", "text": "Machine history / maintenance log", "norm": "TM App-XV, Proforma 4(v)"},
                {"sno": "I1.8", "text": "Staff personal files: appointment, qualification, experience, salary records", "norm": "AN 2.5.4.1"},
                {"sno": "I1.9", "text": "Inspection register; Action Taken Reports on previous inspections", "norm": "TM 2.21(v), 2.25"},
                {"sno": "I1.10", "text": "Minutes of staff meetings", "norm": "TM 2.19"},
                {"sno": "I1.11", "text": "Internal inspection record (Principal / Group Instructor)", "norm": "TM 2.21"},
                {"sno": "I1.12", "text": "Fire / evacuation drill log; water test reports; tank cleaning log", "norm": "AN 10.1, 10.3, 10.6"},
                {"sno": "I1.13", "text": "Complaint register", "norm": "TM Part II 2.3"},
                {"sno": "I1.14", "text": "Placement records and ex-trainee follow-up cards", "norm": "TM 2.15; TM Part II 1.10"},
                {"sno": "I1.15", "text": "Certificate issue register", "norm": "TM App-XV item 12"},
                {"sno": "I1.16", "text": "Statistical returns and portal data submitted on time", "norm": "TM 2.24"},
            ],
        },
        {
            "type": "checklist", "id": "I2", "title": "I2. Governance",
            "rows": [
                _cl("I2.1", "Advisory committee / Institute Management Committee (where constituted) meets regularly; minutes and industry participation", "TM App-XV item 24"),
                _cl("I2.2", "Institute website maintained with prescribed information (trades, staff, admission, affiliation orders)", "TM Part II 1.10(i), Annexure 5"),
                _cl("I2.3", "Institute allowed full inspection and verification; all records produced", "AN 7.2(ix)", star=True),
            ],
        },
    ],
}

J1_GROUNDS = [
    ("i", "(i) Insufficient infrastructure, power, machinery or equipment", "C1, C2, C4, D2.1"),
    ("ii", "(ii) Non-training activity on premises", "Any part (on-site observation)"),
    ("iii", "(iii) Institute closed during working hours", "A7, A12"),
    ("iv", "(iv) Required instructors not available", "E3.1"),
    ("v", "(v) No valid land lease", "C1.1"),
    ("vi", "(vi) Excess fee charged", "F3.7"),
    ("vii", "(vii) Shifted without approval", "B2.4"),
    ("viii", "(viii) Affiliation on false or forged documents", "Any part (documents verified)"),
    ("ix", "(ix) Inspection or verification denied", "I2.3"),
    ("x_xi", "(x)–(xi) Other violations compromising training; malpractice", "Any part"),
]

# J2 rows: part label -> list of block ids (Section A) counted for C/P/N/NA.
J2_ROWS = [
    ("B", "B — Affiliation", ["B2"]),
    ("C", "C — Land, building, infrastructure", ["C1", "C2", "C3", "C4"]),
    ("D", "D — Machinery and equipment", ["D2"]),
    ("E", "E — Staff", ["E3"]),
    ("F", "F — Admissions and training", ["F3", "F4", "F5"]),
    ("G", "G — Assessment", ["G2"]),
    ("H", "H — Safety and welfare", ["H1", "H2", "H3", "H4", "H5", "H6", "H7"]),
    ("I", "I — Records and finance", ["I1", "I2"]),
]

J5_OPTIONS = [
    "Satisfactory — no action beyond routine Action Taken Report.",
    "Satisfactory with deficiencies — Principal / management to remove deficiencies in J3 within the time allowed and submit an Action Taken Report. (AN 3.6(vii) allows 3 months to remove deficiencies in renewal cases.)",
    "Unsatisfactory: critical deficiency found — issue Show Cause Notice within 2 weeks of inspection; reply due within 3 weeks of the notice; refer to RDSDE / SSDEC for de-affiliation or surrender of unit(s) under AN 7.3.1 and Table 18.",
]

J8_TEXT = ("I / We, (full name), (designation), serving at (office), declare that I / we conducted this inspection on "
           "(date) and personally verified the infrastructure, machinery, equipment, staff details and other parameters "
           "recorded above. The information is true and accurate to the best of my / our knowledge, and has been "
           "recorded fairly and without any external influence.")

PART_J = {
    "code": "J",
    "title": "Part J — Findings, recommendation and certification",
    "blocks": [
        {
            "type": "j1", "id": "J1", "title": "J1. Critical deficiencies (grounds for de-affiliation, AN 7.2)",
            "rows": [{"k": k, "ground": g, "linked": l} for k, g, l in J1_GROUNDS],
        },
        {"type": "j2", "id": "J2", "title": "J2. Summary of compliance by part", "rows": [{"k": k, "label": l, "blocks": b} for k, l, b in J2_ROWS]},
        {
            "type": "grid", "id": "J3", "title": "J3. Deficiencies and action required",
            "columns": [
                {"k": "item_ref", "label": "Item ref", "t": "text"},
                {"k": "deficiency", "label": "Deficiency observed", "t": "textarea"},
                {"k": "category", "label": "Category: Critical / Major / Minor", "t": "select", "options": ["Critical", "Major", "Minor"]},
                {"k": "action", "label": "Action required", "t": "textarea"},
                {"k": "responsible", "label": "Responsible", "t": "text"},
                {"k": "time", "label": "Time allowed", "t": "text"},
            ],
            "numbered": True, "min_rows": 4,
        },
        {
            "type": "grid", "id": "J4",
            "title": "J4. Unit-wise recommendation (adapted from AN Ann-15 Part G; for renewal or complaint-based inspections)",
            "columns": [
                {"k": "trade", "label": "Trade", "t": "text"},
                {"k": "aff_s1", "label": "Units affiliated (S1 / S2 / S3) — S1", "short": "Affl. S1", "t": "number"},
                {"k": "aff_s2", "label": "Units affiliated (S1 / S2 / S3) — S2", "short": "S2", "t": "number"},
                {"k": "aff_s3", "label": "Units affiliated (S1 / S2 / S3) — S3", "short": "S3", "t": "number"},
                {"k": "ok_s1", "label": "Units found compliant (S1 / S2 / S3) — S1", "short": "Compliant S1", "t": "number"},
                {"k": "ok_s2", "label": "Units found compliant (S1 / S2 / S3) — S2", "short": "S2", "t": "number"},
                {"k": "ok_s3", "label": "Units found compliant (S1 / S2 / S3) — S3", "short": "S3", "t": "number"},
                {"k": "reason", "label": "Reason for any non-compliant unit: machinery short / not working, workshop or classroom short of area, instructor not available", "short": "Reason for any non-compliant unit", "t": "textarea"},
            ],
            "min_rows": 1,
        },
        {"type": "choice", "id": "J5", "title": "J5. Overall assessment and recommendation (tick one)", "options": J5_OPTIONS},
        {"type": "text", "id": "J6", "title": "J6. Interaction with trainees and instructors (problems reported and suggestions; TM App-XV note)"},
        {"type": "text", "id": "J7", "title": "J7. Final remarks of inspecting team (training arrangements, adequacy of machines, calibre of instructors, discipline of trainees, whether training meets industry needs, suggestions; TM 2.25(vi)(c))"},
        {"type": "declaration", "id": "J8", "title": "J8. Declaration by inspecting member(s) (adapted from AN Ann-15)", "text": J8_TEXT},
    ],
}

SECTION_A = {
    "id": "SA",
    "title": "Section A – Technical Evaluation",
    "parts": [PART_A, PART_B, PART_C, PART_D, PART_E, PART_F, PART_G, PART_H, PART_I, PART_J],
}

# ---------------------------------------------------------------------------
# SECTION B — INSTITUTIONAL OFFICE WORKING AND FINANCIAL MATTERS INSPECTION
# ---------------------------------------------------------------------------

def _ob(sr, no, head, rule):
    return {"sr": sr, "sno": str(no), "text": head, "norm": rule}


_SB_PARTS = [
    ("A", "A. Office Working, Correspondence and Case Monitoring", [
        _ob("i.", 1, "Diary / Dispatch Register", "HP Office Manual (2011), paras 13.1.1 and 13.1.20"),
        _ob("ii.", 2, "File Opening Register", "HP Office Manual, para 13.1.4"),
        _ob("iii.", 3, "Assembly Questions, Short Notice Questions, and other matters Register", "HP Office Manual, para 13.1.6"),
        _ob("iv.", 4, "RTI Application / Disposal Register", "HP RTI Rules, 2006, rule 3(1)"),
        _ob("v.", 5, "CM Seva Sankalp (1100) Complaint Register / Portal Record", "MMSS Helpline @1100 complaint-handling guidelines; portal MIS / action-taken records"),
        _ob("vi.", 6, "Court Cases / Litigation Monitoring Register", "HP Office Manual, para 13.1.21"),
        _ob("vii.", 7, "Peon / Messenger Book", "HP Office Manual, para 13.1.19"),
        _ob("viii.", 8, "Noting Procedure / Notes and Orders on Files", "HP Office Manual, para 11.3"),
    ]),
    ("B", "B. Budget, Finance and Accounts", [
        _ob("i.", 9, "Budget Control / Expenditure Register", "HPFR, 2009, rule 37(4)(b)"),
        _ob("ii.", 10, "Monthly Expenditure Returns and Reconciliation Record", "HPFR, 2009, rules 37(4)(b), 37(5)(b)–(d)"),
        _ob("iii.", 11, "Broadsheet of Expenditure Returns", "HPFR, 2009, rule 37(4)(c) (controlling offices)"),
        _ob("iv.", 12, "Bill Register", "HPFR, 2009, rule 37(5)(a); HPTR, 2017, rule 107"),
        _ob("v.", 13, "Bill Transit Register", "HPTR, 2017, rule 108"),
        _ob("vi.", 14, "Cash Book", "HPFR, 2009, rule 3(7)(b); applicable cash-accounting / departmental instructions (cash-handling offices)"),
        _ob("vii.", 15, "Receipt Book and Treasury Challan Record", "HPFR, 2009, rule 3(1), (5) and (7)(b); applicable Treasury receipt / challan instructions"),
        _ob("viii.", 16, "Surrender of Funds Record", "HPFR, 2009, rules 39 and 41 (surrender of savings); record format as directed"),
        _ob("ix.", 17, "Advance and Recovery Register", "HPFR, 2009, rule 162 (Government loans); relevant advance / recovery instructions"),
        _ob("x.", 18, "Security Deposit / Performance Security Record", "HPFR, 2009, rule 132 (performance security); relevant contract / deposit conditions"),
        _ob("xi.", 19, "Income Tax/TDS Deduction and Deposit Records", "Income-tax Act, 1961, as applicable"),
        _ob("xii.", 20, "GST/TDS Deduction and Deposit Records", "CGST Act, 2017, applicable GST law / notifications"),
        _ob("xiii.", 21, "Scholarship / Stipend Disbursement and Beneficiary Records", "Applicable scholarship / stipend scheme guidelines, sanctions and DBT instructions"),
        _ob("xiv.", 22, "Scheme-wise Financial and Physical Progress Reports", "Applicable scheme guidelines, sanction orders and departmental reporting instructions"),
        _ob("xv.", 23, "Grant-in-Aid Subsidiary Accounts and Utilisation Certificate Record", "HPFR, 2009, rules 156–157 (grant-receiving institutions)"),
    ]),
    ("C", "C. Establishment, Personnel and Service Matters", [
        _ob("i.", 24, "Establishment Register / Sanctioned Strength Register", "HP Office Manual, paras 13.1.7 and 13.1.16"),
        _ob("ii.", 25, "Service Books / e-Service Books", "HPFR, 2009, rule 173; SR 196–203; HP Office Manual, para 13.1.8"),
        _ob("iii.", 26, "Personal Files of Employees", "HP Office Manual, Annexure XIX-A (record retention); applicable service instructions"),
        _ob("iv.", 27, "Attendance Register / Biometric Attendance Record", "HP Office Manual, paras 8.6.2–8.6.3"),
        _ob("v.", 28, "Casual Leave Register", "HP Office Manual, para 8.6.4"),
        _ob("vi.", 29, "Promotion and Transfer Orders Record", "HP Office Manual, paras 13.1.14–13.1.15"),
        _ob("vii.", 30, "Retirement Register / Retirement Due Statement", "HP Office Manual, para 13.1.11; applicable pension instructions"),
        _ob("viii.", 31, "Disciplinary / Vigilance Cases Register", "HP Office Manual, para 13.1.18; applicable CCS (CCA) Rules"),
        _ob("ix.", 32, "Personal Recovery Record", "As per applicable rules"),
        _ob("x.", 33, "Pension, Family Pension and Retirement Benefit Files", "Applicable HP / CCS pension rules (as adopted) and Treasury / AG instructions"),
        _ob("xi.", 34, "Employee Training and Qualification Records", "HP Office Manual, paras 13.1.7–13.1.8 (PMIS)"),
        _ob("xii.", 35, "Property Returns / Permission Records", "CCS (Conduct) Rules, 1964, rule 18, as applicable in Himachal Pradesh"),
        _ob("xiii.", 36, "Employee Advance Recovery Record (HBA/other advances)", "Applicable HBA / other advance rules and recovery sanctions"),
        _ob("xiv.", 37, "GPF/NPS/GIS Deduction and Remittance Records", "Applicable GPF / NPS / GIS rules, subscription and remittance instructions"),
        _ob("xv.", 38, "Record of Increments", "Applicable FR/SR / pay-fixation rules; HP Office Manual"),
        _ob("xvi.", 39, "TA/LTC Check Register", "HPFR, 2009, rules 174 and 176; relevant TA / LTC rules"),
        _ob("xvii.", 40, "Medical Claims Register", "HPFR, 2009, rule 175; applicable medical reimbursement rules"),
    ]),
    ("D", "D. Procurement, Stores, Assets and Inventory", [
        _ob("i.", 41, "Stock Register / Goods Receipt Register", "HPFR, 2009, rule 135(2)–(3)"),
        _ob("ii.", 42, "Consumable Stores / Stationery Account", "HPFR, 2009, rule 138(1)–(2)"),
        _ob("iii.", 43, "Fixed Assets / Equipment Register", "HPFR, 2009, rules 138(2) and 140(1)"),
        _ob("iv.", 44, "Dead Stock / Unserviceable Items Register", "HPFR, 2009, rules 138(2) and 140(1)"),
        _ob("v.", 45, "Stores Receipt and Issue Accounts", "HPFR, 2009, rules 135–136 and 138"),
        _ob("vi.", 46, "Stock Physical Verification Record and Certificate", "HPFR, 2009, rules 140–141 (annual physical verification)"),
        _ob("vii.", 47, "Indent / Requisition Records", "HPFR, 2009, rule 136(1)"),
        _ob("viii.", 48, "Purchase / Tender / Comparative Statement Files", "HPFR, 2009, procurement provisions, GeM orders where applicable"),
        _ob("ix.", 49, "Purchase Orders / Supply Contracts Record", "HPFR, 2009, procurement and contract-management provisions"),
        _ob("x.", 50, "Disposal / Auction / Write-off Records", "HPFR, 2009, rules 145–151"),
        _ob("xi.", 51, "Vehicle Log Books and Repair Records", "HP Office Manual, Annexure XIX-A, item 91 (retention); departmental vehicle instructions"),
        _ob("xii.", 52, "Furniture and Office Equipment Maintenance Records", "HP Office Manual, Annexure XIX-A, item 92 (retention); HPFR, rules 138 and 140"),
        _ob("xiii.", 53, "Hostel, Laboratory, Workshop and Training Equipment Records", "HPFR, 2009, rules 138 and 140; applicable institution / laboratory / hostel rules"),
    ]),
    ("E", "E. Audit, Records and Record-Room Management", [
        _ob("i.", 54, "Register of Files Consigned to Record Room", "HP Office Manual, para 13.1.22"),
        _ob("ii.", 55, "Record Room Receipt / Consignment Lists", "HP Office Manual, paras 19.4–19.6"),
        _ob("iii.", 56, "Record Requisition Slips / Issue Record", "HP Office Manual, para 19.7"),
        _ob("iv.", 57, "Elimination / Destruction Register", "HP Office Manual, para 19.8"),
        _ob("v.", 58, "Audit Inspection Reports, Replies and Compliance Files", "HP Office Manual, Annexure XIX-A, item 87 (retention); applicable audit instructions"),
        _ob("vi.", 59, "Audit Objection Settlement Monitoring Register", "Internal monitoring register recommended; relevant AG / audit compliance instructions"),
        _ob("vii.", 60, "Departmental Rules, Notifications and Circulars Guard File", "HP Office Manual, para 18.11"),
    ]),
    ("F", "F. Student Welfare Fund (SWF) — Government ITIs", [
        _ob("i.", 61, "Fee receipt Register", "Student Welfare Fund Rules, 2025 (Govt. ITIs),"),
        _ob("ii.", 62, "Deposit of Receipt", "Student Welfare Fund Rules, 2025"),
        _ob("iii.", 63, "Cash Book/Pass Book", "Student Welfare Fund Rules, 2025"),
        _ob("iv.", 64, "Ledger", "Student Welfare Fund Rules, 2025"),
        _ob("v.", 65, "Bank Reconciliation Statement", "Student Welfare Fund Rules, 2025"),
        _ob("vi.", 66, "Record of SWF Meeting", "Student Welfare Fund Rules, 2025"),
        _ob("vii.", 67, "Details of Audit Paras (All SWF Heads)", "Student Welfare Fund Rules, 2025"),
        _ob("viii.", 68, "Security Register (SWF)", "Student Welfare Fund Rules, 2025"),
        _ob("ix.", 69, "SWF Audit Inspection Reports, Replies and Compliance Files", "Applicable audit instructions"),
    ]),
    ("G", "G. Institution Management Committee / Internal Revenue Generation (IMC / IRG)", [
        _ob("i.", 70, "Receipt Register", "Applicable approved IMC / IRG bylaws, scheme instructions and fee / receipt orders"),
        _ob("ii.", 71, "Cash Book/Pass Book", "Applicable IMC / IRG financial rules, sanctioned bank-account arrangements and accounting instructions"),
        _ob("iii.", 72, "Ledger", "Approved IMC / IRG accounting procedures and governing council resolutions"),
        _ob("iv.", 73, "Bank Reconciliation Statement", "Applicable IMC / IRG accounting controls and bank-account instructions (periodic reconciliation)"),
        _ob("v.", 74, "Record of IMC/IRG Governing Council meeting", "Applicable IMC constitution / MoA / bylaws and governing council meeting / approval requirements"),
    ]),
]

SECTION_B = {
    "id": "SB",
    "title": "SECTION-B / INSTITUTIONAL OFFICE WORKING AND FINANCIAL MATTERS INSPECTION",
    "parts": [
        {
            "code": code,
            "title": title,
            "govt_only": code == "F",
            "blocks": [{"type": "office", "id": code, "title": title, "rows": rows}],
        }
        for code, title, rows in _SB_PARTS
    ],
}

PROFORMA = {
    "title": PROFORMA_TITLE,
    "version": PROFORMA_VERSION,
    "cpn_options": CPN_OPTIONS,
    "cpn_legend": CPN_LEGEND,
    "star_legend": STAR_LEGEND,
    "sections": [SECTION_A, SECTION_B],
}
