from django.db import models

from tapir.coop.models import ShareOwner


class RizomaMemberData(models.Model):
    photo_id = models.CharField(null=True, max_length=255)
    share_owner = models.OneToOneField(
        ShareOwner,
        null=False,
        on_delete=models.CASCADE,
        related_name="rizoma_member_data",
    )
