# Generated by Django 5.1.2 on 2024-11-08 11:55

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("coop", "0046_deleteincomingpaymentlogentry"),
        ("log", "0007_auto_20240702_1748"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name="logentry",
            index=models.Index(fields=["user"], name="log_logentr_user_id_c4ca60_idx"),
        ),
        migrations.AddIndex(
            model_name="logentry",
            index=models.Index(
                fields=["share_owner"], name="log_logentr_share_o_84d116_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="logentry",
            index=models.Index(
                fields=["created_date"], name="log_logentr_created_d766ab_idx"
            ),
        ),
    ]