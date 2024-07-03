from celery import shared_task
from django.core.management import call_command


@shared_task
def update_purchase_tracking_list():
    call_command("update_purchase_tracking_list")


@shared_task
def send_create_account_reminder():
    call_command("send_create_account_reminder")
