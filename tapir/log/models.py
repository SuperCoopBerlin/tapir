from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner


class LogEntry(models.Model):
    created_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Create Date")
    )

    actor = models.ForeignKey(
        TapirUser, null=True, on_delete=models.CASCADE, related_name="+"
    )

    # User or ShareOwner that this log entry is associated with. Exactly one should be filled
    user = models.ForeignKey(
        TapirUser, related_name="log_entries", null=True, on_delete=models.PROTECT
    )
    share_owner = models.ForeignKey(
        ShareOwner, related_name="log_entries", null=True, on_delete=models.PROTECT
    )

    log_class_type = models.ForeignKey(
        ContentType, on_delete=models.PROTECT, related_name="+"
    )

    # Not abstract to be able to query all log entries, see https://stackoverflow.com/questions/3797982/how-to-query-abstract-class-based-objects-in-django

    def clean(self):
        super().clean()
        if bool(self.user) == bool(self.share_owner):
            raise ValidationError("Exactly one of user and share_owner must be set.")

    def save(self, *args, **kwargs):
        if not hasattr(self, "log_class_type"):
            # for_concrete_model=False makes this also works for proxy models (that don't add any fields themselves
            # but just add rendering)
            self.log_class_type = ContentType.objects.get_for_model(
                self.__class__, for_concrete_model=False
            )
        super(LogEntry, self).save(*args, **kwargs)

    def as_leaf_class(self):
        """
        Returns the log entry as it was when being saved to the database

        Since log entries derive from LogEntry, but access is done via the LogEntry class,
        we need to retrieve the original log entry from its original model which is saved
        as log_class_type.
        """
        if not self.log_class_type:
            return self

        model_class = self.log_class_type.model_class()
        if model_class:
            return model_class.objects.get(pk=self.pk)
        else:
            return self

    def populate(self, actor=None, user=None, share_owner=None):
        self.actor = actor
        self.user = user
        self.share_owner = share_owner

        return self

    def render(self):
        return render_to_string(self.template_name, {"entry": self})


class EmailLogEntry(LogEntry):
    template_name = "log/email_log_entry.html"

    subject = models.CharField(max_length=128)
    email_content = models.BinaryField()

    def populate(self, email_message: EmailMessage, *args, **kwargs):
        self.subject = email_message.subject
        self.email_content = email_message.message().as_bytes()
        return super().populate(*args, **kwargs)
