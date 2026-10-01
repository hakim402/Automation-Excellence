"""
Seeds the SiteSettings singleton with Automex's real company facts.

A data migration rather than a seed command, because these are not demo
content: a fresh deployment needs the right address and phone number in the
database before the site renders anything.

Only facts confirmed in CLAUDE.md are written. Founded year, team size,
social profiles, tagline and the short description are deliberately left
empty -- they have not been supplied, and an invented value would end up in
structured data that search engines read.

Idempotent and non-destructive: it fills blank fields only, so running it
again, or after an admin has edited a value, changes nothing.
"""

from django.db import migrations

# CLAUDE.md section 11, "Company facts".
COMPANY_FACTS = {
    "company_name": "Automex",
    "address_line_1": "827 W Valley Hwy",
    "address_line_2": "Trlr #57",
    "city": "Kent",
    "state": "WA",
    "postal_code": "98032",
    "country": "United States",
    "service_area": "Worldwide",
    "phone_us": "+1 (206) 470-9284",
    "phone_af": "+93 776 320 765",
    "email": "info@automex.tech",
    "domain": "https://automex.tech",
}


def seed_company_facts(apps, _schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")

    settings_row, created = SiteSettings.objects.get_or_create(
        pk=1, defaults=dict(COMPANY_FACTS)
    )

    if created:
        return

    # Fill only what is still blank, so an admin's edits survive.
    changed = []
    for field, value in COMPANY_FACTS.items():
        if not getattr(settings_row, field, None):
            setattr(settings_row, field, value)
            changed.append(field)

    if changed:
        settings_row.save(update_fields=changed)


def unseed(apps, _schema_editor):
    """
    Reversible without data loss: the singleton stays, because deleting it
    would break every page. Reversing simply does nothing.
    """


class Migration(migrations.Migration):
    dependencies = [("core", "0002_initial")]

    operations = [migrations.RunPython(seed_company_facts, unseed)]
