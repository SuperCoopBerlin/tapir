from __future__ import annotations

import datetime
import os
from typing import Type, Callable, List, TYPE_CHECKING

import environ
import ldap
from django.db import models
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.encoding import iri_to_uri
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django_auth_ldap.config import LDAPSearch
from ldap import modlist

from tapir import settings

if TYPE_CHECKING:
    from tapir.accounts.models import TapirUser
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


def get_group_members(connection, group_cn):
    search = LDAPSearch(
        "ou=groups,dc=supercoop,dc=de", ldap.SCOPE_SUBTREE, f"(cn={group_cn})"
    )
    result = search.execute(connection)
    return result[0][1]._data["member"] if result else []


def create_ldap_group(connection, group_cn, tapir_users: List[TapirUser]):
    # Empty groups are not allowed in LDAP, so we need to create them with at least one member
    connection.add_s(
        build_ldap_group_dn(group_cn),
        modlist.addModlist(
            {
                "objectclass": [b"groupOfNames"],
                "member": [
                    tapir_user.build_ldap_dn().encode("utf-8")
                    for tapir_user in tapir_users
                ],
            }
        ),
    )


def set_group_membership(
    tapir_users: List[TapirUser], group_cn, is_member_of_group: bool
):
    connection = get_admin_ldap_connection()

    current_group_members = get_group_members(connection, group_cn)
    groups_exists = (
        len(current_group_members) > 0
    )  # Empty groups can't exist in LDAP, if get_group_members returns an empty the group has not been found

    if not groups_exists:
        if not is_member_of_group:
            return
        create_ldap_group(connection, group_cn, tapir_users)
        return

    current_group_members = get_group_members(connection, group_cn)
    tapir_users_dns = [tapir_user.build_ldap_dn() for tapir_user in tapir_users]

    if is_member_of_group:
        members_to_update = [
            user_dn
            for user_dn in tapir_users_dns
            if user_dn not in current_group_members
        ]
    else:
        members_to_update = [
            user_dn for user_dn in tapir_users_dns if user_dn in current_group_members
        ]

    if not members_to_update:
        return

    if not is_member_of_group and set(members_to_update) == set(current_group_members):
        # Here we would remove all members of the group, so instead we delete the group
        connection.delete_s(build_ldap_group_dn(group_cn))
        return

    group_dn = build_ldap_group_dn(group_cn)
    connection.modify_s(
        group_dn,
        [
            (
                ldap.MOD_ADD if is_member_of_group else ldap.MOD_DELETE,
                "member",
                [member_dn.encode("utf-8") for member_dn in members_to_update],
            )
        ],
    )


def get_admin_ldap_connection():
    connection = ldap.initialize("ldap://openldap")
    connection.simple_bind_s("cn=admin,dc=supercoop,dc=de", "admin")
    return connection


def is_member_in_group(connection, tapir_user: TapirUser, group_cn: str):
    return tapir_user.build_ldap_dn() in get_group_members(connection, group_cn)
