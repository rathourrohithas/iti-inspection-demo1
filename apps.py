from django.apps import AppConfig


class InspectionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inspections"
    verbose_name = "ITI Inspections"

    def ready(self):
        from . import signals  # noqa: F401
