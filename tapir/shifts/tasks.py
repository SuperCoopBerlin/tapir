from celery import shared_task
from django.core.management import call_command


@shared_task
def send_shift_reminders():
    call_command("send_shift_reminders")


@shared_task
def apply_shift_cycle_start():
    call_command("apply_shift_cycle_start")


@shared_task
def generate_shifts():
    call_command("generate_shifts")
