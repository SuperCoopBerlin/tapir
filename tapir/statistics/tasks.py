from celery import shared_task
from django.core.management import call_command


@shared_task
def process_purchase_files():
    call_command("process_purchase_files")


@shared_task
def process_credit_account():
    call_command("process_credit_account")
