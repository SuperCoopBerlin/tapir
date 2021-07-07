from django import template
from django.urls import reverse

from tapir.coop.models import ShareOwner
from tapir.log.forms import CreateTextLogEntryForm
from tapir.log.models import LogEntry

register = template.Library()


@register.inclusion_tag("log/log_entry_list_tag.html", takes_context=True)
def user_log_entry_list(context, selected_user):
    raw_entries = LogEntry.objects.filter(user=selected_user).order_by("-created_date")
    log_entries = [entry.as_leaf_class() for entry in raw_entries]
    context["log_entries"] = log_entries

    context["create_text_log_entry_action_url"] = "%s?next=%s" % (
        reverse("log:create_user_text_log_entry", args=[selected_user.pk]),
        selected_user.get_absolute_url(),
    )

    return context


@register.inclusion_tag("log/log_entry_list_tag.html", takes_context=True)
def share_owner_log_entry_list(context, share_owner):
    raw_entries = LogEntry.objects.filter(share_owner=share_owner).order_by(
        "-created_date"
    )
    log_entries = [entry.as_leaf_class() for entry in raw_entries]
    context["log_entries"] = log_entries

    context["create_text_log_entry_action_url"] = "%s?next=%s" % (
        reverse("log:create_share_owner_text_log_entry", args=[share_owner.pk]),
        share_owner.get_absolute_url(),
    )

    return context
