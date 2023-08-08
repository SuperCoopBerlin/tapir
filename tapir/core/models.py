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
        flag = cls.objects.filter(flag_name=flag_name).first()
        return flag.flag_value if flag else False

    @classmethod
    def set_flag_value(cls, flag_name: str, flag_value: bool):
        flag = cls.objects.get(flag_name=flag_name)
        flag.flag_value = flag_value
        flag.save()
