from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag()
def rizoma_photo_url(photo_id: str) -> str:
    return f"{settings.COOPS_PT_API_BASE_URL}/files/memberPhotos/{photo_id}-thumb.jpg"
