"""
Tests for the admin a non-developer has to operate.

The Phase 1 acceptance test is "I want to click through the admin", so these
assert the things a click-through would reveal: every screen loads, every
translatable form has six tabs with English first, lists carry status badges
and search, and the singleton behaves like one.
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Industry, SiteSettings, Stat, TeamMember, Testimonial, Tool
from apps.services.models import FAQ, ProcessStep, Service, ServiceOffering

TRANSLATABLE_MODELS = [
    SiteSettings,
    Industry,
    Testimonial,
    TeamMember,
    Stat,
    Service,
    ServiceOffering,
    ProcessStep,
    FAQ,
]

ALL_MODELS = [*TRANSLATABLE_MODELS, Tool]


class AdminSmokeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="staff", email="staff@example.com", password="pw-for-tests-only"
        )

    def setUp(self):
        self.client.force_login(self.user)


class AdminReachabilityTests(AdminSmokeTestCase):
    def test_every_changelist_loads(self):
        for model in ALL_MODELS:
            meta = model._meta
            url = reverse(f"admin:{meta.app_label}_{meta.model_name}_changelist")
            with self.subTest(model=meta.model_name):
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200)

    def test_every_add_form_loads(self):
        # SiteSettings is a singleton and deliberately refuses "add".
        for model in [m for m in ALL_MODELS if m is not SiteSettings]:
            meta = model._meta
            url = reverse(f"admin:{meta.app_label}_{meta.model_name}_add")
            with self.subTest(model=meta.model_name):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_every_service_change_form_loads(self):
        for service in Service.objects.all():
            url = reverse("admin:services_service_change", args=[service.pk])
            with self.subTest(service=service.slug):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_dashboard_loads(self):
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)


class LanguageTabTests(AdminSmokeTestCase):
    def test_every_translatable_form_has_six_tabs_english_first(self):
        for model in TRANSLATABLE_MODELS:
            model_admin = admin.site._registry[model]
            fieldsets = model_admin.get_fieldsets(None)
            tabs = [name for name, opts in fieldsets if "tab" in opts.get("classes", ())]

            with self.subTest(model=model._meta.model_name):
                self.assertEqual(len(tabs), 6, f"{model.__name__} tabs: {tabs}")
                self.assertEqual(tabs[0], "English")
                self.assertEqual(tabs, [label for _code, label in settings.LANGUAGES])

    def test_each_tab_holds_only_that_locale_s_fields(self):
        model_admin = admin.site._registry[Service]
        for name, options in model_admin.get_fieldsets(None):
            if "tab" not in options.get("classes", ()):
                continue
            code = next(c for c, label in settings.LANGUAGES if label == name)
            with self.subTest(tab=name):
                for field in options["fields"]:
                    self.assertTrue(field.endswith(f"_{code}"), f"{field} in {name} tab")

    def test_no_translatable_field_is_missing_from_the_tabs(self):
        """A field left out of translated_field_order must still appear."""
        from apps.core.admin_mixins import translated_fields_for

        model_admin = admin.site._registry[Service]
        self.assertEqual(
            set(model_admin.get_translated_fields()),
            set(translated_fields_for(Service)),
        )

    def test_search_metadata_sorts_after_the_prose(self):
        model_admin = admin.site._registry[Service]
        order = model_admin.get_translated_fields()
        self.assertLess(order.index("name"), order.index("meta_title"))
        self.assertLess(order.index("body"), order.index("meta_description"))

    def test_arabic_inputs_are_right_to_left(self):
        """Otherwise a translator cannot see the start of their own sentence."""
        model_admin = admin.site._registry[Service]
        request = None

        rtl = model_admin.formfield_for_dbfield(Service._meta.get_field("intro_ar"), request)
        ltr = model_admin.formfield_for_dbfield(Service._meta.get_field("intro_en"), request)

        self.assertEqual(rtl.widget.attrs.get("dir"), "rtl")
        self.assertEqual(rtl.widget.attrs.get("lang"), "ar")
        self.assertNotIn("dir", ltr.widget.attrs)
        self.assertEqual(ltr.widget.attrs.get("lang"), "en")

    def test_the_form_renders_all_six_tab_labels(self):
        service = Service.objects.get(key="cyber-security")
        response = self.client.get(reverse("admin:services_service_change", args=[service.pk]))
        body = response.content.decode()
        for _code, label in settings.LANGUAGES:
            with self.subTest(label=label):
                self.assertIn(label, body)


class ListViewUsabilityTests(AdminSmokeTestCase):
    """CLAUDE.md section 5: a list a non-developer cannot operate is not done."""

    def test_translatable_lists_show_a_translation_badge(self):
        for model in TRANSLATABLE_MODELS:
            if model is SiteSettings:
                continue  # redirects to the single row, has no list
            model_admin = admin.site._registry[model]
            with self.subTest(model=model._meta.model_name):
                self.assertIn("translation_badge", model_admin.list_display)

    def test_every_list_has_search_and_filters(self):
        for model in ALL_MODELS:
            if model is SiteSettings:
                continue
            model_admin = admin.site._registry[model]
            with self.subTest(model=model._meta.model_name):
                self.assertTrue(model_admin.search_fields, "needs search_fields")
                self.assertTrue(model_admin.list_display, "needs list_display")
                self.assertTrue(model_admin.list_filter, "needs list_filter")

    def test_the_service_list_shows_how_complete_each_page_is(self):
        service = Service.objects.get(key="cyber-security")
        ServiceOffering.objects.create(service=service, title_en="a", description_en="b")
        model_admin = admin.site._registry[Service]
        self.assertIn("1 offerings", model_admin.content_summary(service))

    def test_unfold_theme_is_applied_not_django_s(self):
        response = self.client.get(reverse("admin:services_service_changelist"))
        self.assertIn("unfold/css/styles.css", response.content.decode())


class SingletonAdminTests(AdminSmokeTestCase):
    def test_changelist_redirects_to_the_single_row(self):
        response = self.client.get(reverse("admin:core_sitesettings_changelist"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("admin:core_sitesettings_change", args=[SiteSettings.SINGLETON_PK]),
            response["Location"],
        )

    def test_adding_a_second_row_is_refused(self):
        model_admin = admin.site._registry[SiteSettings]
        self.assertFalse(model_admin.has_add_permission(None))

    def test_deleting_is_refused(self):
        model_admin = admin.site._registry[SiteSettings]
        self.assertFalse(model_admin.has_delete_permission(None))


class SidebarNavigationTests(TestCase):
    """The sidebar is the per-service navigator, so its links must resolve."""

    def test_every_navigation_link_points_at_a_real_admin_url(self):
        from django.urls import resolve

        from config.admin_navigation import NAVIGATION

        for group in NAVIGATION:
            for item in group["items"]:
                with self.subTest(item=item["title"]):
                    self.assertTrue(resolve(item["link"].split("?", 1)[0]), item["link"])

    def test_groups_are_named_as_the_spec_describes(self):
        from config.admin_navigation import NAVIGATION

        self.assertEqual(
            [group["title"] for group in NAVIGATION],
            [
                "Dashboard",
                "Site",
                "Services",
                "Products",
                "Media",
                "Digital Marketing",
                "AI & Automation",
                "Custom Software",
                "Web Development",
                "Mobile Development",
                "Cyber Security",
                "Content",
                "Leads",
                "System",
            ],
        )
