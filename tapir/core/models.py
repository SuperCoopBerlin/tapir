from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class FeatureFlag(models.Model):
    flag_name = models.CharField(
        _("Flag name"), max_length=300, blank=False, null=False
    )
    flag_value = models.BooleanField(
        _("Flag value"), default=False, blank=False, null=False
    )

    @classmethod
    def get_flag_value(cls, flag_name: str) -> bool:
        return cls.objects.get_or_create(
            flag_name=flag_name, defaults={"flag_value": False}
        )[0].flag_value

    @classmethod
    def set_flag_value(cls, flag_name: str, flag_value: bool):
        flag = cls.objects.get(flag_name=flag_name)
        flag.flag_value = flag_value
        flag.save()

    @classmethod
    def ensure_flag_exists(cls, flag_name):
        if cls.objects.filter(flag_name=flag_name).exists():
            return
        cls.objects.create(flag_name=flag_name)


class NonDeleted(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteMixin(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        abstract = True

    objects = NonDeleted()
    everything = models.Manager()

    def soft_delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"], using=using)

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
