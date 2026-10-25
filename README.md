# Online ITI Inspection Portal

Directorate of Technical Education, Vocational & Industrial Training, Himachal Pradesh.

This web application digitises the approved **ITI Inspection Proforma**:
- Section A – Technical Evaluation, Parts A–J.
- Section B – Institutional Office Working and Financial Matters, Parts A–G.

Inspection teams use it to enter data during their visits, and the Directorate uses it to monitor and retrieve the records.

- **Form:** 298 items and 776 input fields, in the original order, wording and numbering. See `docs/FIELD_MAP.xlsx`.
- **Roles:**
  - Administrator, at the Directorate.
  - Directorate officer, with read-only monitoring.
  - Inspecting officer, who acts as team leader or team member for a given inspection.
- **Works on** desktop, tablet and mobile browsers. It can be installed to the phone home screen. If connectivity drops, it keeps entries on the device and sends them when the connection returns.

---

## 1. What the portal does

| Requirement (project brief) | Where it is in the portal |
|---|---|
| Login, user management, role-based access | **Users** page. Accounts created by the administrator must change their password at first login. Login locks for 15 minutes after 5 failed attempts. |
| ITI master list, import | **ITIs**: add/edit, or import Excel/CSV (template provided). Ownership (Govt / Private) decides whether Section B Part F (SWF) applies. |
| Inspection assignment and scheduling | **Schedule**: ITI, team name, visit date, deadline, team leader, team members, and parts each member may edit. Bulk import from Excel/CSV. |
| Digital proforma | **My inspections → Start / Continue**. One part per screen with a part menu, *Save draft*, *Save and continue*, autosave, answered-item markers and a progress bar. |
| Photographs and documents | Every item has **Take photo** (opens the phone camera) and **Attach file**. JPG, JPEG, PNG and PDF are accepted; the size limit is set in **Settings**. Uploads are never compulsory. |
| Offline drafts | Entries made without a connection are kept on the device and sent automatically when back online. The form page reopens offline if it was opened once on that device. Photos are uploaded once online. |
| Validation | Numbers, dates, times, e-mail, phone and coordinates are checked. Mandatory items are only those the administrator ticks in **Settings**, since the proforma marks none. |
| Review and submission | **Review & submit**: completeness by part, blank items, mandatory items, and J8 declarations. Only the team leader can make the final submission, after a confirmation step. The form then locks, and duplicate submissions are blocked. |
| Return / reopen | The administrator can **return a submitted form for correction**, with a recorded reason. The team edits and resubmits. |
| Audit trail | **Audit log**: every field change (old → new value), uploads, removals, submissions, returns, logins, exports and settings changes, with user, time and IP. |
| Directorate dashboard | **Dashboard** shows: total, not started, in progress, submitted, and pending beyond deadline; district-wise and team-wise progress; and ITI-wise status with visit, inspection and submission dates. Filters: district, ITI, team, dates, status. |
| Search and retrieval | **Records**: search and filter, open any record, and download each as PDF or Excel. |
| Completed proforma (PDF / Excel) | **PDF** follows the proforma's section order, numbering, tables and wording, with responses filled in. It ends with an annexure of photographs and documents, and drafts are watermarked. **Excel** has one sheet per Part, laid out like the proforma. |
| Bulk export | **Records → Export Excel / CSV**. "All responses" gives one row per answered field with Section, Part, S.No and wording. "Compliance matrix" gives one row per ITI with every C/P/N, Y/N and the J2 counts. |
| Calculations | J2 is computed automatically from C/P/N responses. G1 pass % is computed from appeared and passed. No other scoring is added. |

### Corrections applied to the proforma

These were approved by the Directorate and are listed in the portal under **Settings → Notes on the digital proforma**, as well as in `docs/CORRECTIONS.md`.

1. D2 items printed as D2.10–D2.16 are renumbered D2.9–D2.15.
2. J1 linked items:
   - (ii) A15 → *Any part (on-site observation)*
   - (iii) A14 → *A7, A12*
   - (viii) I2.8 → *Any part (documents verified)*
   - (ix) I2.9 → *I2.3*
3. A ★ legend is added: critical item linked to a J1 de-affiliation ground.
4. **NA** is added to every C/P/N column, to match the NA column of J2.
5. In J2, Part I counts I1 registers as follows:
   - Maintained Y + Up to date Y = C
   - Maintained Y + Up to date N = P
   - Maintained N = N
6. Section B Part F (SWF) is shown only for Government ITIs.
7. J8 "Signature" is an electronic declaration by each logged-in member, with date and time. The signed page and the Principal's acknowledgement can also be uploaded.

---

## 2. Installing on a government server (Docker)

**Requirements:**
- A Linux server (e.g. NIC / State Data Centre VM) with Docker and the Docker Compose plugin.
- A domain name.
- A TLS certificate for that domain.

```bash
# 1. Copy this folder to the server, then:
cp .env.example .env
nano .env        # set DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS, POSTGRES_PASSWORD
#   Generate a secret key:  python3 -c "import secrets; print(secrets.token_urlsafe(60))"

# 2. Put the certificate in deploy/certs/fullchain.pem and deploy/certs/privkey.pem

# 3. Start everything (PostgreSQL, the portal, nginx, daily backups)
docker compose up -d --build

# 4. Create the first administrator
docker compose exec web python manage.py createsuperuser
```

Then open `https://<your-domain>/`, sign in, and work through these screens:
1. **ITIs** – import the ITI list.
2. **Users** – create officer accounts.
3. **Schedule** – assign inspections.
4. **Settings** – optionally tick mandatory items and set upload size.

**Upgrades:**
```bash
docker compose up -d --build
```
This applies any database migrations automatically.

**Without Docker**, any Linux host with Python 3.11+ and PostgreSQL 14+ also works:
```bash
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
python manage.py migrate && python manage.py createcachetable && python manage.py collectstatic --noinput
gunicorn portal.wsgi:application --bind 127.0.0.1:8000 --workers 4
```
Put it behind nginx or Apache with HTTPS, using `deploy/nginx.conf` as a guide.

---

## 3. Security

- **Transport:** HTTPS only. HTTP redirects to HTTPS, HSTS is on, and cookies are secure and HTTP-only. Content-Security-Policy and X-Frame-Options are set.
- **Passwords:**
  - Hashed with PBKDF2.
  - Minimum 10 characters, with common and numeric-only passwords rejected.
  - Must be changed at first login.
- **Login:** temporary lockout after repeated failures. Sessions expire after 10 hours.
- **Access control:**
  - Inspectors see only inspections assigned to them.
  - Members can edit only the parts the administrator assigns.
  - Only the leader submits.
  - Directorate officers have read-only access.
- **Uploads:**
  - Type and size are checked, and file content is checked against the extension.
  - Files are stored outside the web root and served only after an access check. Nothing is publicly reachable.
- **Encryption at rest:** use the hosting platform's encrypted disk or volume for the PostgreSQL data, uploaded-file volume and backups. This is standard on NIC / SDC and approved clouds.
- **Audit log:** cannot be edited or deleted from the application.

## 4. Backups and recovery

- The `backup` service runs every night at `BACKUP_HOUR` (default 02:00). It writes a PostgreSQL dump and an archive of the uploaded files to `./backups/`, and keeps them for `BACKUP_KEEP_DAYS` (default 30).
- Copy `./backups/` to separate storage, such as the SDC backup share, on a schedule.
- To run a backup now:
  ```bash
  docker compose exec backup /app/deploy/backup.sh
  ```
- To restore:
  ```bash
  ./deploy/restore.sh backups/db_YYYYMMDD_HHMM.dump backups/media_YYYYMMDD_HHMM.tar.gz
  ```

## 5. Training and testing data

```bash
docker compose exec web python manage.py seed_demo           # sample ITIs, officers and inspections, all marked "(Sample)"
docker compose exec web python manage.py seed_demo --reset   # remove and recreate them
```
- Sample logins: `sample.admin`, `sample.viewer`, `sample.lead1`, `sample.mem1` (and others). For a public practice site on Render, see `docs/DEMO_DEPLOY.md`.
- Password: `Sample@2026pass`.
- Remove the sample data before going live by deleting the "(Sample)" ITIs and `sample.*` users, or use a fresh database.

## 6. For developers

- **Proforma wording, numbering, norms and references:** `inspections/proforma.py` is the single source. Do not change wording without an approved amendment. After any change, run `python manage.py export_field_map` and the tests.
- **Server-side logic:** validation, progress and the J2 calculation are in `inspections/schema.py`. Data entry, autosave and offline handling are in `inspections/static/inspections/form.js`.
- **Outputs:** PDF is in `inspections/reports.py`, Excel/CSV in `inspections/exports.py`, and the shared table layout in `inspections/tables.py`.
- **Tests:**
  ```bash
  DJANGO_DEBUG=1 python manage.py test inspections
  ```
  These cover:
  - Fidelity: every numbered item is present.
  - Section permissions, validation and calculations.
  - Declarations, submission locking, duplicate prevention and return for correction.
  - Audit trail, upload rules, exports, imports and login lockout.
- **Local run:**
  ```bash
  DJANGO_DEBUG=1 python manage.py migrate && DJANGO_DEBUG=1 python manage.py runserver
  ```
  This uses SQLite.
