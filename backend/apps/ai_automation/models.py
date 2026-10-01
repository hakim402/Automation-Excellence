from django.db import models

from apps.core.models import (
    Ordered,
    Publishable,
    validate_icon_name,
    validate_slug_is_english,
)
from apps.core.uploads import (
    UploadTo,
    validate_image_file,
    validate_upload_size,
)
from apps.portfolio.models import CaseStudy


class AutomationUseCase(Publishable, Ordered):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    description = models.TextField()
    industry = models.ForeignKey(
        "core.Industry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="automation_use_cases",
    )
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.title


class AgentType(Publishable, Ordered):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])
    example_prompt = models.TextField(
        blank=True, help_text="Plain text example, without confidential customer data."
    )

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class Integration(Publishable, Ordered):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])

    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])
    logo = models.ImageField(
        upload_to=UploadTo("integrations"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    url = models.URLField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=[
            ("llm", "LLM"),
            ("workflow", "Workflow"),
            ("data", "Data"),
            ("crm", "CRM"),
            ("comms", "Communications"),
        ],
    )

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class AIAutomationCaseStudy(CaseStudy):
    service_key = "ai-automation"

    class Meta:
        proxy = True
        verbose_name = "Case study"
        verbose_name_plural = "Case studies"
