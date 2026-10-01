"""
Creates the six service lines.

These are not demo content: the six names, slugs and keys are fixed business
facts from BUILD_PROMPT.md, and `Service.key` is a closed choice set. A fresh
database needs all six rows before any service page can exist.

Only the identity fields are written. Headlines, intros, bodies, offerings
and process steps are marketing copy that has not been supplied, so they
stay empty and the admin's "Content" column shows each page as still thin.

Icons are Material Symbols names -- a design choice, not a business fact.

Idempotent: fills blanks only, never overwrites an edited row.
"""

from django.db import migrations

SERVICES = [
    {
        "key": "digital-marketing",
        "slug": "digital-marketing",
        "name": "Digital Marketing",
        "icon": "campaign",
        "order": 10,
    },
    {
        "key": "ai-automation",
        "slug": "ai-automation",
        "name": "AI & Automation",
        "icon": "smart_toy",
        "order": 20,
    },
    {
        "key": "custom-software",
        "slug": "custom-software",
        "name": "Custom Software Development",
        "icon": "database",
        "order": 30,
    },
    {
        "key": "web-development",
        "slug": "web-development",
        "name": "Web App Development",
        "icon": "language",
        "order": 40,
    },
    {
        "key": "mobile-development",
        "slug": "mobile-development",
        "name": "Mobile App Development",
        "icon": "smartphone",
        "order": 50,
    },
    {
        "key": "cyber-security",
        "slug": "cyber-security",
        "name": "Cyber Security",
        "icon": "encrypted",
        "order": 60,
    },
]


def create_services(apps, _schema_editor):
    Service = apps.get_model("services", "Service")

    for spec in SERVICES:
        # name is translated, so the real column is name_en. English is the
        # source of truth and the other five locales fall back to it.
        defaults = {
            "slug": spec["slug"],
            "name": spec["name"],
            "name_en": spec["name"],
            "icon": spec["icon"],
            "order": spec["order"],
            "is_active": True,
        }
        service, created = Service.objects.get_or_create(key=spec["key"], defaults=defaults)

        if created:
            continue

        changed = []
        for field, value in defaults.items():
            if not getattr(service, field, None):
                setattr(service, field, value)
                changed.append(field)
        if changed:
            service.save(update_fields=changed)


def remove_services(apps, _schema_editor):
    Service = apps.get_model("services", "Service")
    Service.objects.filter(key__in=[spec["key"] for spec in SERVICES]).delete()


class Migration(migrations.Migration):
    dependencies = [("services", "0001_initial")]

    operations = [migrations.RunPython(create_services, remove_services)]
