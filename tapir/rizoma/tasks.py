from celery import shared_task
from django.core.management import call_command


@shared_task
def sync_users_with_coops_pt_backend():
    call_command("sync_users_with_coops_pt_backend")
