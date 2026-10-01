"""
The /api/v1/ surface. App routers are mounted here as they are built.

Every read endpoint is public, read-only and accepts ?lang=<locale>.
Write endpoints exist only under crm/.
"""

from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def api_root(_request):
    """Discovery document. Kept honest as endpoints are added."""
    return Response({"version": "v1", "endpoints": []})


urlpatterns = [
    path("", api_root, name="api-root"),
]
