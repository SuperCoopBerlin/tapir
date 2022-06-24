from django import template
from django.urls import reverse
from datetime import datetime, timedelta
from tapir.log.models import LogEntry

register = template.Library()


@register.inclusion_tag("log/log_entry_list_tag.html", takes_context=True)
def log_entry_list(context, **kwargs):
    # check if user or shareowner is in kwargs and is length one
    if not any(key in kwargs for key in ("user", "sharewoner")) or len(kwargs) > 1:
        raise ValueError

    last_x_days = 30
    raw_entries = LogEntry.objects.filter(
        **kwargs,
        created_date__gte=datetime.now()
        - timedelta(days=last_x_days),  # show only the last x days
    ).order_by("-created_date")
    log_entries = [entry.as_leaf_class() for entry in raw_entries]
    context["log_entries"] = log_entries

    key, val = next(iter(kwargs.items()))
    context["create_text_log_entry_action_url"] = "%s?next=%s" % (
        reverse(f"log:create_{key}_text_log_entry", args=[val.pk]),
        val.get_absolute_url(),
    )

    return context
