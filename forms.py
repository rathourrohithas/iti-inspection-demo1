from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.conf import settings

from .models import ITI, Inspection, Profile

User = get_user_model()


def _attempt_key(request, username):
    ip = (request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
          or request.META.get("REMOTE_ADDR", ""))
    return f"login-fail:{(username or '').lower()}:{ip}"


class LockoutAuthenticationForm(AuthenticationForm):
    """Standard login with temporary lockout after repeated failures."""

    def clean(self):
        username = self.data.get("username", "")
        key = _attempt_key(self.request, username)
        if cache.get(key, 0) >= settings.LOGIN_MAX_ATTEMPTS:
            raise forms.ValidationError(
                f"Too many failed attempts. Please try again after {settings.LOGIN_LOCKOUT_MINUTES} minutes.",
                code="locked")
        try:
            return super().clean()
        except forms.ValidationError:
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, settings.LOGIN_LOCKOUT_MINUTES * 60)
            raise


class UserForm(forms.Form):
    username = forms.RegexField(regex=r"^[\w.@+-]{3,150}$", max_length=150,
                                help_text="Login ID: letters, digits and . @ + - _ only.")
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)
    designation = forms.CharField(max_length=150, required=False)
    office = forms.CharField(max_length=200, required=False)
    mobile = forms.CharField(max_length=20, required=False)
    is_active = forms.BooleanField(required=False, initial=True, label="Account active")
    password = forms.CharField(widget=forms.PasswordInput, required=False,
                               help_text="Temporary password (min. 10 characters). The user must change it at first login. "
                                         "Leave blank when editing to keep the current password.")

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is None:
            self.fields["password"].required = True

    def clean_username(self):
        u = self.cleaned_data["username"]
        qs = User.objects.filter(username__iexact=u)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This login ID is already in use.")
        return u

    def clean_password(self):
        pw = self.cleaned_data.get("password")
        if pw:
            validate_password(pw)
        return pw

    def save(self):
        cd = self.cleaned_data
        u = self.instance or User(username=cd["username"])
        u.username = cd["username"]
        parts = cd["full_name"].strip().split(" ", 1)
        u.first_name = parts[0]
        u.last_name = parts[1] if len(parts) > 1 else ""
        u.email = cd["email"]
        u.is_active = cd["is_active"]
        if cd.get("password"):
            u.set_password(cd["password"])
        u.save()
        prof, _ = Profile.objects.get_or_create(user=u)
        prof.role = cd["role"]
        prof.designation = cd["designation"]
        prof.office = cd["office"]
        prof.mobile = cd["mobile"]
        if cd.get("password"):
            prof.must_change_password = True
        prof.save()
        return u


class ITIForm(forms.ModelForm):
    class Meta:
        model = ITI
        fields = ["name", "mis_code", "ownership", "district", "block", "address",
                  "principal_name", "principal_mobile", "principal_email", "active"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}


def inspector_choices():
    return User.objects.filter(is_active=True, profile__role=Profile.INSPECTOR).order_by("first_name", "username")


class AssignmentForm(forms.ModelForm):
    leader = forms.ModelChoiceField(queryset=User.objects.none(), label="Team leader")
    members = forms.ModelMultipleChoiceField(queryset=User.objects.none(), required=False,
                                             label="Team members",
                                             widget=forms.SelectMultiple(attrs={"size": 8}),
                                             help_text="Hold Ctrl (or long-press on mobile) to choose several.")

    class Meta:
        model = Inspection
        fields = ["iti", "team_name", "scheduled_date", "deadline"]
        widgets = {
            "scheduled_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "deadline": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = inspector_choices()
        self.fields["leader"].queryset = qs
        self.fields["members"].queryset = qs
        self.fields["iti"].queryset = ITI.objects.filter(active=True)
        self.fields["leader"].label_from_instance = self.fields["members"].label_from_instance = \
            lambda u: f"{u.get_full_name() or u.username} — {getattr(u.profile, 'designation', '')}"

    def clean(self):
        cd = super().clean()
        if cd.get("scheduled_date") and cd.get("deadline") and cd["deadline"] < cd["scheduled_date"]:
            self.add_error("deadline", "Deadline cannot be before the scheduled date.")
        if cd.get("leader") and cd.get("members") and cd["leader"] in cd["members"]:
            cd["members"] = [m for m in cd["members"] if m != cd["leader"]]
        return cd


class ImportForm(forms.Form):
    file = forms.FileField(help_text="Excel (.xlsx) or CSV file in the template format.")


class SettingsForm(forms.Form):
    max_upload_mb = forms.IntegerField(min_value=1, max_value=50, label="Maximum file size per upload (MB)")
    allowed_types = forms.MultipleChoiceField(
        choices=[("jpg", "JPG"), ("jpeg", "JPEG"), ("png", "PNG"), ("pdf", "PDF")],
        widget=forms.CheckboxSelectMultiple, label="Allowed file types")
