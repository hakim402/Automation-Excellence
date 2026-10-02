"""Add labeled drafts for review without rewriting real company content or publishing."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.ai_automation.models import AgentType, AutomationUseCase, Integration
from apps.blog.models import Category, Post, Tag
from apps.core.models import TeamMember
from apps.custom_software.models import DatabaseCapability, SystemType
from apps.cyber_security.models import SecurityService
from apps.digital_marketing.models import Campaign
from apps.mobile_development.models import MobileApp
from apps.portfolio.models import CaseStudy, CaseStudyMetric
from apps.products.models import Product, ProductFeature
from apps.services.models import FAQ, ProcessStep, Service, ServiceOffering
from apps.web_development.models import WebCapability

DEMO = "DEMO — placeholder only. Replace with approved content before publishing."


class Command(BaseCommand):
    help = "Create clearly labeled demo drafts; keep existing records and translations untouched."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo seeding is available only in development (DEBUG=True).")
        created_count = 0

        def create(model, lookup, **defaults):
            nonlocal created_count
            obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
            if created:
                obj.full_clean()
                created_count += 1
            return obj, created

        services = list(Service.objects.all())
        if len(services) != 6:
            raise CommandError("Apply migrations first; the six service records must exist.")
        for service in services:
            # Child demo records attach only to drafts, never change a live service page.
            if service.status == "published":
                continue
            create(
                ServiceOffering,
                {"service": service, "title_en": "DEMO offering"},
                description_en=DEMO,
                icon="widgets",
            )
            create(
                ProcessStep,
                {"service": service, "title_en": "DEMO discovery step"},
                description_en=DEMO,
                order=1,
            )
            create(
                FAQ,
                {"service": service, "question_en": "DEMO: how does the process work?"},
                answer_en=f"<p>{DEMO}</p>",
            )
            case, created = create(
                CaseStudy,
                {"slug": f"demo-{service.key}-case-study"},
                service=service,
                title_en=f"DEMO {service.name_en} case study",
                client_name="DEMO — no real client",
                challenge_en=f"<p>{DEMO}</p>",
                solution_en=f"<p>{DEMO}</p>",
                outcome_en=f"<p>{DEMO}</p>",
            )
            if created:
                create(
                    CaseStudyMetric,
                    {"case_study": case, "label_en": "DEMO metric — not a result"},
                    value="—",
                )

        product, created = create(
            Product,
            {"slug": "demo-workflow-template"},
            name_en="DEMO workflow template",
            tagline_en="DEMO — not an available product",
            category="template",
            summary_en=DEMO,
            body_en=f"<p>{DEMO}</p>",
            delivery="customisable",
        )
        if created:
            product.services.add(Service.objects.get(key="ai-automation"))
            create(
                ProductFeature,
                {"product": product, "title_en": "DEMO feature"},
                description_en=DEMO,
            )

        author, _ = create(
            TeamMember,
            {"name": "DEMO author — not a team member"},
            role_en="DEMO author",
            bio_en=DEMO,
            is_active=False,
        )
        category, _ = create(
            Category, {"slug": "demo-category"}, name_en="DEMO category", description_en=DEMO
        )
        tag, _ = create(Tag, {"slug": "demo-tag"}, name_en="DEMO tag")
        post, created = create(
            Post,
            {"slug": "demo-editorial-preview"},
            title_en="DEMO editorial preview",
            excerpt_en=DEMO,
            body_en=f"<p>{DEMO}</p>",
            author=author,
            category=category,
        )
        if created:
            post.tags.add(tag)

        for model, slug, defaults in (
            (
                Campaign,
                "demo-campaign",
                {
                    "title_en": "DEMO campaign",
                    "client_name": "DEMO — no real client",
                    "objective_en": DEMO,
                    "summary_en": DEMO,
                },
            ),
            (
                AutomationUseCase,
                "demo-workflow",
                {"title_en": "DEMO workflow", "description_en": DEMO},
            ),
            (AgentType, "demo-assistant", {"name_en": "DEMO assistant", "description_en": DEMO}),
            (Integration, "demo-integration", {"name": "DEMO integration", "category": "workflow"}),
            (SystemType, "demo-system", {"name_en": "DEMO system", "description_en": DEMO}),
            (
                DatabaseCapability,
                "demo-database",
                {"name_en": "DEMO database capability", "description_en": DEMO},
            ),
            (WebCapability, "demo-web", {"name_en": "DEMO web capability", "description_en": DEMO}),
            (
                MobileApp,
                "demo-mobile",
                {
                    "name": "DEMO mobile app",
                    "description_en": DEMO,
                    "platforms": ["ios", "android"],
                },
            ),
            (
                SecurityService,
                "demo-security",
                {"name_en": "DEMO security service", "description_en": DEMO},
            ),
        ):
            create(model, {"slug": slug}, **defaults)
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} demo records. "
                "Existing content was kept; nothing was published. "
                "Media, certifications, real claims and CRM submissions "
                "are intentionally not fabricated."
            )
        )
