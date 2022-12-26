from celery import shared_task
from django.core.management import call_command


@shared_task
def update_purchase_tracking_list():
    call_command("update_purchase_tracking_list")
