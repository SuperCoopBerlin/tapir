from django import template

from tapir.accounts.models import TapirUser
from tapir.utils.user_utils import UserUtils

register = template.Library()


@register.simple_tag
def get_display_name_for_viewer(person, request_user: TapirUser):
    return UserUtils.build_display_name_for_viewer(person, request_user)


@register.simple_tag
def get_display_name_full(person):
    return UserUtils.build_display_name(person, UserUtils.DISPLAY_NAME_TYPE_FULL)


@register.simple_tag
def get_display_name_short(person):
    return UserUtils.build_display_name(person, UserUtils.DISPLAY_NAME_TYPE_SHORT)


@register.simple_tag
def get_display_name_legal(person):
    return UserUtils.build_display_name_legal(person)


@register.simple_tag
def get_html_link(person, request_user: TapirUser):
    return UserUtils.build_html_link_for_viewer(person, request_user)
