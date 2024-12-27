from tapir.coop.models import ShareOwner
from tapir.utils.user_utils import UserUtils


def get_display_name_for_welcome_desk(share_owner: ShareOwner, request_user) -> str:
    display_type = UserUtils.should_viewer_see_short_or_long_display_type(request_user)
    if display_type == UserUtils.DISPLAY_NAME_TYPE_SHORT:
        display_type = UserUtils.DISPLAY_NAME_TYPE_WELCOME_DESK
    return UserUtils.build_display_name(share_owner, display_type)
