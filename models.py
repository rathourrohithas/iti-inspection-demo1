import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"
    INSPECTOR = "INSPECTOR"
    ROLE_CHOICES = [
        (ADMIN, "Administrator (Directorate)"),
        (VIEWER, "Directorate officer (monitoring, read-only)"),
        (INSPECTOR, "Inspecting officer (team leader / member)"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default=INSPECTOR)
    designation = models.CharField(max_length=150, blank=True)
    office = models.CharField(max_length=200, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class ITI(models.Model):
    GOVT = "GOVT"
    PRIVATE = "PRIVATE"
    OWNERSHIP = [(GOVT, "Government"), (PRIVATE, "Private")]
    name = models.CharField("Name of ITI", max_length=250)
    mis_code = models.CharField("MIS code", max_length=50, unique=True)
    ownership = models.CharField(max_length=10, choices=OWNERSHIP, default=GOVT)
    district = models.CharField(max_length=100)
    block = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    principal_name = models.CharField(max_length=150, blank=True)
    principal_mobile = models.CharField(max_length=20, blank=True)
    principal_email = models.EmailField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["district", "name"]
        verbose_name = "ITI"
        verbose_name_plural = "ITIs"

    def __str__(self):
        return f"{self.name} ({self.mis_code})"

    @property
    def is_govt(self):
        return self.ownership == self.GOVT


class Inspection(models.Model):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    RETURNED = "RETURNED"
    STATUS_CHOICES = [
        (NOT_STARTED, "Not started"),
        (IN_PROGRESS, "In progress"),
        (SUBMITTED, "Submitted"),
        (RETURNED, "Returned for correction"),
    ]
    iti = models.ForeignKey(ITI, on_delete=models.PROTECT, related_name="inspections")
    team_name = models.CharField(max_length=150)
    scheduled_date = models.DateField("Scheduled date of visit")
    deadline = models.DateField("Submission deadline")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=NOT_STARTED, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    version = models.PositiveIntegerField(default=0)
    progress_pct = models.PositiveSmallIntegerField(default=0)
    proforma_version = models.CharField(max_length=20, blank=True)
    return_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        ordering = ["-scheduled_date", "iti__name"]

    def __str__(self):
        return f"{self.iti.name} — {self.scheduled_date}"

    @property
    def is_locked(self):
        return self.status == self.SUBMITTED

    @property
    def is_overdue(self):
        return self.status != self.SUBMITTED and self.deadline < timezone.localdate()

    @property
    def inspection_date(self):
        v = (self.data or {}).get("SA.A7.date") or ""
        if len(v) == 10 and v[4] == "-":
            return f"{v[8:10]}-{v[5:7]}-{v[0:4]}"
        return v

    def leader(self):
        tm = self.team.filter(role=TeamMember.LEADER).select_related("user", "user__profile").first()
        return tm.user if tm else None

    def membership(self, user):
        return self.team.filter(user=user).first()


class TeamMember(models.Model):
    LEADER = "LEADER"
    MEMBER = "MEMBER"
    ROLE_CHOICES = [(LEADER, "Team leader"), (MEMBER, "Team member")]
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="team")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inspection_roles")
    role = models.CharField(max_length=8, choices=ROLE_CHOICES, default=MEMBER)
    # Part keys (e.g. "SA.C", "SB.B") this member may edit. Empty = all parts.
    sections = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = [("inspection", "user")]
        ordering = ["-role", "id"]

    def can_edit_part(self, part_key):
        if self.role == self.LEADER or not self.sections:
            return True
        return part_key in self.sections


def upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"inspections/{instance.inspection_id}/{uuid.uuid4().hex}{ext}"


class Attachment(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="attachments")
    unit_key = models.CharField(max_length=60, db_index=True)
    file = models.FileField(upload_to=upload_path)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    caption = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["uploaded_at"]

    @property
    def is_image(self):
        return self.content_type.startswith("image/")


class AuditLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    inspection = models.ForeignKey(Inspection, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit")
    action = models.CharField(max_length=40, db_index=True)
    field_key = models.CharField(max_length=80, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    details = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]


class PortalSettings(models.Model):
    """Single-row configuration editable by the administrator."""
    max_upload_mb = models.PositiveSmallIntegerField(default=10)
    allowed_types = models.CharField(max_length=100, default="jpg,jpeg,png,pdf")
    # Unit keys (e.g. "SA.A1", "SA.B2.1") that must be answered before submission.
    mandatory_units = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def allowed_ext_list(self):
        return [e.strip().lower().lstrip(".") for e in self.allowed_types.split(",") if e.strip()]
