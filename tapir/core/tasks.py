import socket

from celery import shared_task
from celery.signals import task_failure
from django.core.mail import mail_admins
from django.core.management import call_command


@shared_task
def metabase_export():
    call_command("metabase_export")


@task_failure.connect()
def celery_task_failure_email(**kwargs):
    subject = (
        "[Django][{queue_name}@{host}] Error: Task {sender.name} ({task_id})".format(
            queue_name="celery",  # `sender.queue` doesn't exist in 4.1?
            host=socket.gethostname(),
            **kwargs,
        )
    )
    message = """Task {sender.name} with id {task_id} raised exception: {exception!r}
                 Task was called with args: {args} kwargs: {kwargs}.
                 The contents of the full traceback was:{einfo}.
              """.format(**kwargs)
    mail_admins(subject, message)
