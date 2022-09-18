from celery import shared_task
from django.core.management import call_command


@shared_task
def send_accounting_recap():
    call_command("send_accounting_recap")
