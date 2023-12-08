import datetime
import os
from typing import Type, Callable

import environ
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.encoding import iri_to_uri
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from tapir.log.models import UpdateModelLogEntry


def safe_redirect(redirect_url, default, request):
    if redirect_url is None:
        return redirect(default)

    if not url_has_allowed_host_and_scheme(
        url=redirect_url, allowed_hosts=None, require_https=request.is_secure()
    ):
        return redirect("/")

    url = iri_to_uri(redirect_url)
    return redirect(url)


def get_monday(date: datetime.date):
    return date - datetime.timedelta(days=date.weekday())


def get_first_of_next_month(date: datetime.date):
    return (date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)


def get_first_of_previous_first_day_of_month(date: datetime.date):
    if date.day != 1:
        return date.replace(day=1)
    return (date - datetime.timedelta(days=2)).replace(day=1)


def set_header_for_file_download(response: HttpResponse, filename: str):
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)


def get_html_link(url: str, text: str):
    return format_html("<a href={}>{}</a>", url, text)


def get_timezone_aware_datetime(
    date: datetime.date, time: datetime.time
) -> datetime.datetime:
    result = datetime.datetime.combine(date, time)
    return (
        timezone.make_aware(result, is_dst=False)
        if timezone.is_naive(result)
        else result
    )


def setup_ssh_for_biooffice_storage():
    env = environ.Env()

    os.system("mkdir -p ~/.ssh")
    os.system(
        f'bash -c \'echo -e "{env("TAPIR_SSH_KEY_PRIVATE")}" > ~/.ssh/biooffice_id_rsa\''
    )
    os.system("chmod u=rw,g=,o= ~/.ssh/biooffice_id_rsa")
    os.system(
        f'bash -c \'echo -e "{env("TAPIR_SSH_KEY_PUBLIC")}" > ~/.ssh/biooffice_id_rsa.pub\''
    )
    os.system("chmod u=rw,g=r,o=r ~/.ssh/biooffice_id_rsa.pub")
    os.system(
        f'bash -c \'echo -e "{env("BIOOFFICE_SERVER_SSH_KEY_FINGERPRINT")}" > ~/.ssh/biooffice_known_hosts\''
    )


def get_models_with_attribute_value_at_date(
    model_class: Type[models.Model],
    log_class: Type[UpdateModelLogEntry],
    attribute_name: str,
    attribute_value: any,
    date: datetime.date,
    entry_to_user: Callable[[models.Model], models.Model] | None = None,
    entry_to_share_owner: Callable[[models.Model], models.Model] | None = None,
):
    if not entry_to_user and not entry_to_share_owner:
        raise ValueError("Must specify either entry_to_user or entry_to_share_owner")

    entries = model_class.objects.all()
    logs = log_class.objects.filter(
        created_date__gte=get_timezone_aware_datetime(
            date, datetime.time(hour=0, minute=0)
        ),
        old_values__has_key=attribute_name,
    )
    result = []
    for entry in entries:
        if entry_to_user:
            log_filter = Q(user=entry_to_user(entry))
        else:
            log_filter = Q(share_owner=entry_to_share_owner(entry))

        entry_logs = logs.filter(log_filter)
        if entry_logs.exists():
            if (
                logs.order_by("created_date").first().old_values[attribute_name]
                == attribute_value
            ):
                result.append(entry)
            continue

        if getattr(entry, attribute_name) == attribute_value:
            result.append(entry)
    return result
