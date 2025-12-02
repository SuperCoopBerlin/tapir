from celery import shared_task
from django.core.management import call_command


@shared_task
def sync_users_with_coops_pt_backend():
    call_command("sync_users_with_coops_pt_backend")


@shared_task
def check_members_group_affiliation():
    call_command("check_members_group_affiliation")
