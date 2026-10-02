"""Exercise the public API against PostgreSQL, including nested publication boundaries."""

from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import translation
from rest_framework.test import APIClient

from apps.ai_automation.models import AgentType, AutomationUseCase
from apps.blog.models import Category, Post, Tag
from apps.core.models import Industry, SiteSettings, Stat, TeamMember, Testimonial, Tool, Video
from apps.core.public_queries import products
from apps.crm.models import Lead, NewsletterSubscriber
from apps.mobile_development.models import MobileApp, MobileAppScreenshot
from apps.portfolio.models import CaseStudy, CaseStudyImage, CaseStudyMetric
from apps.products.models import Product, ProductFeature, ProductImage
from apps.services.models import FAQ, ProcessStep, Service, ServiceOffering
from apps.services.page import SPECIFIC_CONTENT


class PublicAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service = Service.objects.get(key="ai-automation")
        cls.service.status = "published"
        cls.service.name_ar = "الذكاء الاصطناعي"
        cls.service.intro_en = "English introduction"
        cls.service.save()
        cls.industry = Industry.objects.create(name_en="Example industry", slug="example")
        cls.tool = Tool.objects.create(name="Python", slug="python", category="backend")
        cls.service.industries.add(cls.industry)
        cls.service.tools.add(cls.tool)
        cls.product = Product.objects.create(
            name_en="Example product",
            name_ar="منتج",
            slug="example-product",
            category="template",
            summary_en="Summary",
            body_en="<p>Safe body</p>",
            delivery="customisable",
            status="published",
        )
        cls.product.services.add(cls.service)
        cls.case = CaseStudy.objects.create(
            title_en="Example case",
            slug="example-case",
            client_name="Fixture only",
            service=cls.service,
            industry=cls.industry,
            challenge_en="Challenge",
            solution_en="Solution",
            outcome_en="Outcome",
            is_featured=True,
            status="published",
        )
        cls.author = TeamMember.objects.create(name="Fixture author", role_en="Writer")
        cls.category = Category.objects.create(name_en="Category", slug="category")
        cls.tag = Tag.objects.create(name_en="Tag", slug="tag")
        cls.post = Post.objects.create(
            title_en="Post",
            slug="post",
            excerpt_en="Excerpt",
            body_en="<p>Body</p>",
            author=cls.author,
            category=cls.category,
            service=cls.service,
            status="published",
        )
        cls.post.tags.add(cls.tag)
        for state, label in (("none", "visible"), ("machine", "hidden")):
            ServiceOffering.objects.create(
                service=cls.service, title_en=label, description_en=label, translation_status=state
            )
            ProcessStep.objects.create(
                service=cls.service, title_en=label, description_en=label, translation_status=state
            )
            FAQ.objects.create(
                service=cls.service,
                question_en=label,
                answer_en=f"<p>{label}</p>",
                translation_status=state,
            )
            Stat.objects.create(
                service=cls.service, label_en=label, value="12", translation_status=state
            )
            ProductFeature.objects.create(
                product=cls.product, title_en=label, description_en=label, translation_status=state
            )
            ProductImage.objects.create(
                product=cls.product,
                image=f"fixtures/{label}.png",
                caption_en=label,
                translation_status=state,
            )
            CaseStudyMetric.objects.create(
                case_study=cls.case, label_en=label, value="12", translation_status=state
            )
            CaseStudyImage.objects.create(
                case_study=cls.case,
                image=f"fixtures/{label}.png",
                caption_en=label,
                translation_status=state,
            )
            Testimonial.objects.create(
                client_name=label,
                quote_en=label,
                service=cls.service,
                status="published",
                translation_status=state,
            )
            AgentType.objects.create(
                name_en=label, slug=label, status="published", translation_status=state
            )
        Video.objects.create(
            title_en="Example video",
            slug="example-video",
            product=cls.product,
            source="youtube",
            external_url="https://www.youtube.com/watch?v=fixture",
            orientation="portrait",
            status="published",
        )

    def setUp(self):
        self.client = APIClient()

    def get(self, path, **params):
        response = self.client.get("/api/v1/" + path, params)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_all_documented_endpoints_and_public_read_only_methods(self):
        for path in (
            "site/settings/",
            "services/",
            "services/ai-automation/",
            "services/ai-automation/case-studies/",
            "products/",
            "products/example-product/",
            "videos/",
            "portfolio/case-studies/",
            "portfolio/case-studies/example-case/",
            "blog/posts/",
            "blog/posts/post/",
            "blog/categories/",
            "team/",
            "testimonials/",
            "seo/sitemap/",
        ):
            with self.subTest(path=path):
                self.get(path)
                self.assertEqual(
                    self.client.post("/api/v1/" + path, {}, format="json").status_code, 405
                )
        self.assertEqual(self.client.get("/api/v1/products/not-found/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/crm/leads/").status_code, 405)
        self.assertEqual(self.client.get("/api/v1/crm/newsletter/").status_code, 405)
        self.assertEqual(self.client.get("/api/v1/crm/leads/1/").status_code, 404)

    def test_six_locales_fall_back_per_field_independent_of_active_language(self):
        with translation.override("fr"):
            for code, _ in settings.LANGUAGES:
                data = self.get("services/ai-automation/", lang=code)
                self.assertEqual(
                    data["name"], self.service.name_ar if code == "ar" else self.service.name_en
                )
                self.assertEqual(data["intro"], "English introduction")
                self.assertEqual(data["slug"], "ai-automation")
                self.assertNotIn("name_en", data)
            self.assertEqual(
                self.get("services/ai-automation/", lang="invalid")["name"], self.service.name_en
            )
        Service.objects.filter(pk=self.service.pk).update(intro_ar="   ")
        self.assertEqual(
            self.get("services/ai-automation/", lang="ar")["intro"], "English introduction"
        )

    def test_drafts_machine_translations_and_inactive_services_are_never_public(self):
        for field, value in (
            ("status", "draft"),
            ("translation_status", "machine"),
            ("is_active", False),
        ):
            Service.objects.filter(pk=self.service.pk).update(**{field: value})
            for path in (
                "services/ai-automation/",
                "services/ai-automation/case-studies/",
                "portfolio/case-studies/example-case/",
                "blog/posts/post/",
            ):
                self.assertEqual(self.client.get("/api/v1/" + path).status_code, 404)
            self.assertEqual(self.get("services/"), [])
            self.assertEqual(self.get("testimonials/"), [])
            self.assertEqual(self.get("products/example-product/")["services"], [])
            Service.objects.filter(pk=self.service.pk).update(
                status="published", translation_status="none", is_active=True
            )
        for model, obj, path in (
            (Product, self.product, "products/example-product/"),
            (CaseStudy, self.case, "portfolio/case-studies/example-case/"),
            (Post, self.post, "blog/posts/post/"),
        ):
            model.objects.filter(pk=obj.pk).update(translation_status="machine")
            self.assertEqual(self.client.get("/api/v1/" + path).status_code, 404)

    def test_full_service_payload_filters_every_nested_collection(self):
        data = self.get("services/ai-automation/", lang="ar")
        for field in (
            "offerings",
            "process_steps",
            "faqs",
            "stats",
            "testimonials",
            "case_studies",
            "products",
            "tools",
            "industries",
        ):
            self.assertEqual(len(data[field]), 1, field)
        self.assertEqual(len(data["specific_content"]["agent_types"]), 1)
        self.assertEqual(data["products"][0]["name"], "منتج")
        self.assertNotIn("hidden", str(data))

    def test_product_and_portfolio_details_exclude_unreviewed_children(self):
        product = self.get("products/example-product/")
        case = self.get("portfolio/case-studies/example-case/")
        for data, fields in (
            (product, ("features", "gallery", "videos")),
            (case, ("metrics", "gallery")),
        ):
            for field in fields:
                self.assertEqual(len(data[field]), 1)
            self.assertNotIn("hidden", str(data))
        self.assertEqual(product["body"], "<p>Safe body</p>")
        self.assertTrue(product["gallery"][0]["image"].startswith("http://testserver/media/"))

    def test_hidden_author_category_industry_tags_are_omitted_from_public_records(self):
        for obj in (self.author, self.category, self.industry, self.tag):
            obj.translation_status = "machine"
            obj.save()
        post = self.get("blog/posts/post/")
        self.assertIsNone(post["author"])
        self.assertIsNone(post["category"])
        self.assertEqual(post["tags"], [])
        self.assertEqual(self.get("blog/categories/"), [])
        self.assertEqual(self.get("team/"), [])
        self.assertIsNone(self.get("portfolio/case-studies/example-case/")["industry"])
        self.assertEqual(self.get("blog/posts/", category="category")["count"], 0)
        self.assertEqual(self.get("blog/posts/", tag="tag")["count"], 0)
        self.assertEqual(self.get("portfolio/case-studies/", industry="example")["count"], 0)

    def test_video_owner_gates_include_owning_case_study_service(self):
        Video.objects.create(
            title_en="Case clip",
            slug="case-clip",
            case_study=self.case,
            source="vimeo",
            external_url="https://vimeo.com/1",
            orientation="landscape",
            status="published",
        )
        self.assertEqual(len(self.get("videos/")), 2)
        Product.objects.filter(pk=self.product.pk).update(status="draft")
        Service.objects.filter(pk=self.service.pk).update(status="draft")
        self.assertEqual(self.get("videos/"), [])

    def test_filters_pagination_are_stable_and_do_not_filter_detail_routes(self):
        self.assertEqual(
            self.get("products/", category="template", service="ai-automation")["count"], 1
        )
        self.assertEqual(self.get("products/", category="missing")["count"], 0)
        self.assertEqual(
            self.get("blog/posts/", category="category", tag="tag", service="ai-automation")[
                "count"
            ],
            1,
        )
        self.assertEqual(
            self.get("portfolio/case-studies/", industry="example", service="ai-automation")[
                "count"
            ],
            1,
        )
        self.assertEqual(
            len(
                self.get(
                    "videos/", orientation="portrait", product="example-product", featured="false"
                )
            ),
            1,
        )
        self.assertEqual(self.client.get("/api/v1/videos/?featured=bad").status_code, 400)
        for i in range(14):
            Product.objects.create(
                name_en=f"Product {i}",
                slug=f"p-{i}",
                category="template",
                summary_en="Summary",
                delivery="customisable",
                status="published",
            )
        page = self.get("products/", lang="ar", page=2)
        self.assertEqual(page["count"], 15)
        self.assertEqual(len(page["results"]), 3)
        self.assertIn("lang=ar", page["previous"])
        self.assertEqual(self.client.get("/api/v1/products/?page=999").status_code, 404)
        self.get("products/example-product/", category="missing")

    def test_settings_hide_internal_phone_and_unreviewed_settings(self):
        data = self.get("site/settings/")
        self.assertEqual(data["phone_af"], "")
        self.assertNotIn("show_phone_af_publicly", data)
        self.assertNotIn("SECRET", str(data))
        SiteSettings.objects.filter(pk=1).update(show_phone_af_publicly=True)
        self.assertTrue(self.get("site/settings/")["phone_af"])
        SiteSettings.objects.filter(pk=1).update(translation_status="machine")
        self.assertEqual(self.client.get("/api/v1/site/settings/").status_code, 404)

    def test_sitemap_has_six_locales_and_never_drafts_or_noindex(self):
        Product.objects.filter(pk=self.product.pk).update(noindex=True)
        data = self.get("seo/sitemap/")
        self.assertEqual({row["locale"] for row in data}, dict(settings.LANGUAGES).keys())
        self.assertFalse(any("example-product" in row["url"] for row in data))
        self.assertFalse(any("web-development" in row["url"] for row in data))
        urls = [row["url"] for row in data]
        self.assertEqual(len(urls), len(set(urls)))
        for row in data:
            self.assertEqual(len(row["alternates"]), 7)
            self.assertTrue(row["url"].startswith(settings.SITE_DOMAIN))
        self.assertTrue(any(row["url"].endswith("/ar/ai-automation") for row in data))

    def test_etag_requires_revalidation_and_changes_when_unpublished(self):
        response = self.client.get("/api/v1/services/")
        self.assertIn("must-revalidate", response["Cache-Control"])
        self.assertEqual(
            self.client.get("/api/v1/services/", HTTP_IF_NONE_MATCH=response["ETag"]).status_code,
            304,
        )
        Service.objects.filter(pk=self.service.pk).update(status="draft")
        newer = self.client.get("/api/v1/services/", HTTP_IF_NONE_MATCH=response["ETag"])
        self.assertEqual(newer.status_code, 200)
        self.assertEqual(newer.json(), [])

    def test_all_six_service_specific_sections_render_and_respect_publication(self):
        for key, entries in SPECIFIC_CONTENT.items():
            Service.objects.filter(key=key).update(status="published")
            data = self.get(f"services/{key}/")
            self.assertEqual(set(data["specific_content"]), {entry[0] for entry in entries})
        app = MobileApp.objects.create(
            name="Mobile fixture",
            slug="mobile-fixture",
            platforms=["ios"],
            description_en="Description",
            status="published",
        )
        for state in ("none", "machine"):
            MobileAppScreenshot.objects.create(
                app=app, image="fixtures/mobile.png", caption_en=state, translation_status=state
            )
        app_data = self.get("services/mobile-development/")["specific_content"]["apps"]
        self.assertEqual(len(app_data[0]["screenshots"]), 1)

    def test_query_counts_do_not_grow_per_related_record(self):
        with CaptureQueriesContext(connection) as initial:
            self.get("services/ai-automation/")
        for i in range(8):
            AutomationUseCase.objects.create(
                title_en=f"Use {i}",
                slug=f"use-{i}",
                description_en="Fixture",
                industry=self.industry,
                status="published",
            )
            CaseStudy.objects.create(
                title_en=f"Case {i}",
                slug=f"case-{i}",
                client_name="Fixture",
                service=self.service,
                industry=self.industry,
                challenge_en="C",
                solution_en="S",
                outcome_en="O",
                status="published",
                is_featured=True,
            )
        with CaptureQueriesContext(connection) as expanded:
            self.get("services/ai-automation/")
        self.assertEqual(len(initial), len(expanded))
        self.assertLessEqual(len(expanded), 22)
        with CaptureQueriesContext(connection) as listing:
            list(products(detail=True))
        self.assertLessEqual(len(listing), 8)


@override_settings(DEBUG=True)
class DemoSeedTests(TestCase):
    def test_seed_is_idempotent_preserves_edits_and_never_publishes_or_sends_mail(self):
        before = list(Service.objects.values("pk", "name_en", "status", "translation_status"))
        call_command("seed_demo", stdout=StringIO())
        product = Product.objects.get(slug="demo-workflow-template")
        product.name_en = "Edited demo title"
        product.save()
        count = Product.objects.count()
        output = StringIO()
        call_command("seed_demo", stdout=output)
        self.assertIn("Created 0", output.getvalue())
        self.assertEqual(Product.objects.count(), count)
        product.refresh_from_db()
        self.assertEqual(product.name_en, "Edited demo title")
        self.assertEqual(
            list(Service.objects.values("pk", "name_en", "status", "translation_status")), before
        )
        for model in (Product, CaseStudy, Post):
            self.assertFalse(model.objects.published().exists())
        self.assertFalse(
            TeamMember.objects.filter(name__startswith="DEMO", is_active=True).exists()
        )
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(NewsletterSubscriber.objects.count(), 0)

    @override_settings(DEBUG=False)
    def test_demo_seed_refuses_production(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", stdout=StringIO())

    def test_seed_does_not_add_placeholders_to_published_services(self):
        Service.objects.filter(key="ai-automation").update(status="published")
        call_command("seed_demo", stdout=StringIO())
        self.assertFalse(ServiceOffering.objects.filter(service__key="ai-automation").exists())
