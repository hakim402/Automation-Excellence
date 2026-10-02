from apps.core.api import PublicSerializer

from .models import FAQ, ProcessStep, Service, ServiceOffering


class ServiceOfferingSerializer(PublicSerializer):
    class Meta:
        model = ServiceOffering
        fields = ("title", "description", "icon", "order")


class ProcessStepSerializer(PublicSerializer):
    class Meta:
        model = ProcessStep
        fields = ("title", "description", "order")


class FAQSerializer(PublicSerializer):
    class Meta:
        model = FAQ
        fields = ("question", "answer")


class ServiceSummarySerializer(PublicSerializer):
    class Meta:
        model = Service
        fields = ("key", "slug", "name", "icon", "intro", "hero_image")
