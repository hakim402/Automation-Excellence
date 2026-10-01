"""
Translatable fields for the core app.

Human prose only. Slugs, enum keys, tool names, client names, URLs and
numbers are never translated (CLAUDE.md section 5) — a Spanish visitor still
needs to read "PostgreSQL" and still needs /es/cyber-security to resolve.

Adding a field here creates six database columns, so it needs a migration.
"""

from modeltranslation.translator import TranslationOptions, register

from .models import Industry, SiteSettings, Stat, TeamMember, Testimonial


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ("tagline", "about_short", "default_meta_title", "default_meta_description")
    # company_name is a proper noun. Addresses and phone numbers are data.


@register(Industry)
class IndustryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Testimonial)
class TestimonialTranslationOptions(TranslationOptions):
    # The quote itself is translated so a Spanish visitor can read it; the
    # client's name and company are not.
    fields = ("client_role", "quote")


@register(TeamMember)
class TeamMemberTranslationOptions(TranslationOptions):
    fields = ("role", "bio")


@register(Stat)
class StatTranslationOptions(TranslationOptions):
    # The label is prose. The value and the unit are numbers.
    fields = ("label",)


# Tool is deliberately absent: a tool's name is a product name.
