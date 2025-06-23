from celery import shared_task
from django.core.management import call_command


@shared_task
def fetch_users_from_coops_pt():
    call_command("fetch_users_from_coops_pt")
