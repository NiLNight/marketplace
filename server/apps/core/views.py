"""
Views для core приложения.
"""
import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint для мониторинга."""
    logger.info("Health check endpoint was hit!")
    return JsonResponse({'status': 'ok'}) 