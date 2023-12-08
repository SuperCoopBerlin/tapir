from django.db import models
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
