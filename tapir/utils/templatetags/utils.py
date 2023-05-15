from django import template

from tapir.accounts.models import TapirUser
from tapir.utils.user_utils import UserUtils

register = template.Library()


@register.simple_tag
def get_display_name(person, request_user: TapirUser):
    return UserUtils.build_display_name_for_viewer(person, request_user)


@register.simple_tag
def get_html_link(person, request_user: TapirUser):
    return UserUtils.build_html_link_for_viewer(person, request_user)
