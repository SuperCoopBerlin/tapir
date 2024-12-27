from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from tapir.log.util import freeze_for_log


class LogEntry(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["share_owner"]),
            models.Index(fields=["created_date"]),
        ]

    created_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Creation Date")
    )

    actor = models.ForeignKey(
        "accounts.TapirUser", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    # User or ShareOwner that this log entry is associated with. Exactly one should be filled
    user = models.ForeignKey(
        "accounts.TapirUser",
        related_name="log_entries",
        null=True,
        on_delete=models.CASCADE,
    )
    share_owner = models.ForeignKey(
        "coop.ShareOwner",
        related_name="log_entries",
        null=True,
        on_delete=models.CASCADE,
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

    def populate_base(self, actor=None, tapir_user=None, share_owner=None):
        """Populate the log entry model fields.

        This should be used instead of the normal model creation mechanism to do event-specific info extraction logic
        to be done in the log entry class instead of the call sites. For example, for a LogEntry subclass recording an
        email that was sent, callers should only have to pass in the email, how that email should be saved is decided
        by the log entry class instead."""

        self.actor = actor
        self.user = tapir_user
        self.share_owner = share_owner

        if self.share_owner and hasattr(self.share_owner, "user"):
            self.user = self.share_owner.user

        # Prefer user over share_owner
        if self.share_owner and self.user:
            self.share_owner = None

        return self

    def get_context_data(self):
        """Return the context data for the template rendering this LogEntry."""
        return {"entry": self}

    def render(self):
        """Render this LogEntry"""
        return render_to_string(self.template_name, self.get_context_data())

    @classmethod
    def verbose_log_name(cls):
        return cls._meta.verbose_name.title()


class EmailLogEntry(LogEntry):
    """EmailLogEntry logs a sent email message."""

    template_name = "log/email_log_entry.html"

    email_id = models.CharField(
        max_length=128, null=False, blank=False, default="unknown"
    )
    subject = models.CharField(max_length=128, null=True, blank=True)
    email_content = models.BinaryField(null=True)

    def populate(
        self,
        email_id: str,
        email_message: EmailMessage,
        actor=None,
        tapir_user=None,
        share_owner=None,
    ):
        self.email_id = email_id
        if email_message is not None:
            self.subject = email_message.subject[:128]
            self.email_content = email_message.message().as_bytes()
        return super().populate_base(
            actor=actor, tapir_user=tapir_user, share_owner=share_owner
        )

    def get_name(self) -> str:
        # Must import locally to avoid import loop.
        from tapir.core.tapir_email_base import all_emails

        if self.email_id is not None and self.email_id in all_emails.keys():
            return all_emails[self.email_id].get_name()
        return _("Not available")


class TextLogEntry(LogEntry):
    """TextLogEntry logs a manual textual notes.

    This entry type should only be used for manual, user-entered text. For log entries created as a side effect of
    another action, please create an event-specific LogEntry.
    """

    template_name = "log/text_log_entry.html"

    text = models.TextField(blank=False)

    def populate(self, actor, share_owner=None, tapir_user=None):
        # The value for the text field is set by a CreateTextLogEntryForm
        return super().populate_base(
            actor=actor, share_owner=share_owner, tapir_user=tapir_user
        )


class UpdateModelLogEntry(LogEntry):
    old_values = HStoreField()
    new_values = HStoreField()

    class Meta:
        abstract = True

    def populate_base(
        self,
        actor=None,
        tapir_user=None,
        share_owner=None,
        old_frozen: dict | None = None,
        new_frozen: dict | None = None,
        old_model=None,
        new_model=None,
    ):
        if old_model:
            old_frozen = freeze_for_log(old_model)
        if new_model:
            new_frozen = freeze_for_log(new_model)

        # List must not change during iteration
        keys = list(old_frozen.keys())
        # Only record changed
        for k in keys:
            if old_frozen.get(k, None) != new_frozen.get(k, None):
                # HStoreField stores strings only
                old_frozen[k] = str(old_frozen[k])
                new_frozen[k] = str(new_frozen[k])
            else:
                del old_frozen[k]
                del new_frozen[k]

        self.old_values = old_frozen
        self.new_values = new_frozen

        return super().populate_base(
            actor=actor, tapir_user=tapir_user, share_owner=share_owner
        )

    def get_context_data(self):
        context = super().get_context_data()

        changes = []
        for k in self.old_values.keys():
            if hasattr(self, "excluded_fields") and k in self.excluded_fields:
                continue
            changes.append((k, self.old_values[k], self.new_values[k]))
        context["changes"] = changes

        return context


class ModelLogEntry(LogEntry):
    values = HStoreField()

    class Meta:
        abstract = True

    def populate_base(
        self,
        actor=None,
        share_owner=None,
        tapir_user=None,
        frozen=None,
        model=None,
    ):
        frozen = freeze_for_log(model) if model else frozen

        if hasattr(self, "exclude_fields"):
            for k in self.exclude_fields:
                del frozen[k]

        self.values = frozen
        return super().populate_base(
            actor=actor, share_owner=share_owner, tapir_user=tapir_user
        )

    def get_context_data(self):
        context = super().get_context_data()
        context["values"] = (
            self.values.items() if hasattr(self.values, "items") else self.values
        )
        return context
