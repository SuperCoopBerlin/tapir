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
def get_display_name_welcome_desk(person):
    return UserUtils.build_display_name(
        person, UserUtils.DISPLAY_NAME_TYPE_WELCOME_DESK
    )


@register.simple_tag
def get_display_name_legal(person):
    return UserUtils.build_display_name_legal(person)


@register.simple_tag
def get_html_link(person, request_user: TapirUser):
    return UserUtils.build_html_link_for_viewer(person, request_user)


@register.simple_tag
def disabled_if_user_cant_receive_solidarity(user):
    if (
        user.shift_user_data.get_available_solidarity_shifts()
        and user.shift_user_data.get_account_balance() < 0
        and user.shift_user_data.get_used_solidarity_shifts_current_year() < 2
    ):
        return ""
    return "disabled"


@register.simple_tag
def disabled_if_user_cant_give_solidarity(user):
    if user.shift_user_data.is_balance_positive():
        return ""
    return "disabled"
