from apps.core.api import PublicRelated, PublicSerializer
from apps.core.serializers import IndustrySerializer

from .models import AgentType, AutomationUseCase, Integration


class AgentTypeSerializer(PublicSerializer):
    class Meta:
        model = AgentType
        fields = ("name", "slug", "description", "icon", "example_prompt")


class IntegrationSerializer(PublicSerializer):
    class Meta:
        model = Integration
        fields = ("name", "slug", "logo", "url", "category")


class AutomationUseCaseSerializer(PublicSerializer):
    industry = PublicRelated(IndustrySerializer)

    class Meta:
        model = AutomationUseCase
        fields = ("title", "slug", "description", "industry", "icon")
