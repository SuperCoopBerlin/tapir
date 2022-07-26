from datetime import datetime, timedelta

from django import template
from django.db.models import Q
from django.urls import reverse

from tapir.log.models import LogEntry

register = template.Library()


@register.inclusion_tag("log/log_entry_list_tag.html", takes_context=True)
def log_entry_list(context, **kwargs):
    tapir_user = kwargs.get("tapir_user")
    share_owner = kwargs.get("share_owner")

    if not tapir_user and not share_owner:
        raise ValueError(
            "One of 'tapir_user' or 'share_owner' is required as parameter of this tag"
        )

    log_entries = LogEntry.objects.filter(
        created_date__gte=datetime.now() - timedelta(days=30),
    ).order_by("-created_date")

    if tapir_user:
        member = tapir_user
        member_type = "tapir_user"
        filters = Q(user__id=tapir_user.id)
        if hasattr(tapir_user, "share_owner"):
            filters = filters | Q(share_owner__id=tapir_user.share_owner.id)
    else:
        member = share_owner
        member_type = "share_owner"
        filters = Q(share_owner__id=share_owner.id) | Q(
            user__share_owner=share_owner.id
        )
    log_entries = log_entries.filter(filters).distinct()

    log_entries = [entry.as_leaf_class() for entry in log_entries]
    context["log_entries"] = log_entries

    share_owner_id = None
    if tapir_user and hasattr(tapir_user, "share_owner"):
        share_owner_id = tapir_user.share_owner.id
    elif share_owner:
        share_owner_id = share_owner.id
    context["share_owner_id"] = share_owner_id

    context["create_text_log_entry_action_url"] = reverse(
        f"log:create_text_log_entry", args=[member_type, member.id]
    )

    return context
