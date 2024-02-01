from celery import shared_task
from django.core.management import call_command


@shared_task
def metabase_export():
    call_command("metabase_export")
