import datetime
import os
from typing import Type, Callable

import environ
from django.db import models
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.encoding import iri_to_uri
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from tapir import settings
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


def send_file_to_storage_server(filename: str, username: str):
    if settings.DEBUG:
        print(
            f"File '{filename}' won't be sent to the storage server because this is a debug instance."
        )
        return

    setup_ssh_for_biooffice_storage()
    os.system(
        f"scp -o 'NumberOfPasswordPrompts=0' -o 'UserKnownHostsFile=~/.ssh/biooffice_known_hosts' -i ~/.ssh/biooffice_id_rsa -P 23 {filename} {username}@u326634.your-storagebox.de:./"
    )


def get_models_with_attribute_value_at_date(
    entries: QuerySet,
    log_class: Type[UpdateModelLogEntry],
    attribute_name: str,
    attribute_value: any,
    date: datetime.date,
    entry_to_user: Callable[[models.Model], models.Model] | None = None,
    entry_to_share_owner: Callable[[models.Model], models.Model] | None = None,
):
    if not entry_to_user and not entry_to_share_owner:
        raise ValueError("Must specify either entry_to_user or entry_to_share_owner")

    logs = (
        log_class.objects.filter(
            created_date__gte=get_timezone_aware_datetime(
                date, datetime.time(hour=0, minute=0)
            ),
            old_values__has_key=attribute_name,
        )
        .order_by("user", "created_date")
        .select_related("user", "share_owner")
    )  # ordering by user then calling distinct("user") will give us the oldest entry for each user

    if entry_to_user:
        logs = logs.distinct("user")
        logs = {log.user.id: log for log in logs}
    else:
        logs = logs.distinct("share_owner")
        logs = {log.share_owner.id: log for log in logs}

    result = []
    for entry in entries:
        if entry_to_user:
            log = logs.get(entry_to_user(entry).id, None)
        else:
            log = logs.get(entry_to_share_owner(entry).id, None)

        if log:
            if log.old_values[attribute_name] == attribute_value:
                result.append(entry)
            continue

        if getattr(entry, attribute_name) == attribute_value:
            result.append(entry)
    return result


def build_ldap_group_dn(group_cn: str):
    return f"cn={group_cn},ou=groups,dc=supercoop,dc=de"
