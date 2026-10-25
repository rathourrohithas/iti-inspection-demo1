from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import audit
from .models import Profile


@receiver(post_save, sender=get_user_model())
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            user=instance, defaults={"role": Profile.ADMIN if instance.is_superuser else Profile.INSPECTOR})


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    audit.log(request, "LOGIN", user=user)


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if user:
        audit.log(request, "LOGOUT", user=user)


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    audit.log(request, "LOGIN_FAILED", user=None, details=f"username={credentials.get('username', '')[:150]}")
