from django import template

from tapir.coop.models import ShareOwner
from tapir.log.models import LogEntry

register = template.Library()


@register.inclusion_tag("log/log_entry_list_tag.html", takes_context=True)
def user_log_entry_list(context, user):
    raw_entries = LogEntry.objects.filter(user=user).order_by("-created_date")
    log_entries = [entry.as_leaf_class() for entry in raw_entries]
    context["log_entries"] = log_entries
    return context


@register.inclusion_tag("log/log_entry_list_tag.html", takes_context=True)
def share_owner_log_entry_list(context, share_owner):
    raw_entries = LogEntry.objects.filter(share_owner=share_owner).order_by(
        "-created_date"
    )
    log_entries = [entry.as_leaf_class() for entry in raw_entries]
    context["log_entries"] = log_entries
    return context
