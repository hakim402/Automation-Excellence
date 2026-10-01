from django.apps import AppConfig


class CustomSoftwareConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.custom_software"
    verbose_name = "Custom Software"
