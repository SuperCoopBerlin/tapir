# Generated by Django 3.2.23 on 2024-04-21 18:51

import django.contrib.postgres.fields
from django.db import migrations, models
import ldapdb.models.fields
import tapir.core.tapir_email_base


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_auto_20230605_0951"),
    ]

    operations = [
        migrations.AddField(
            model_name="tapiruser",
            name="wanted_emails",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        (
                            "tapir.shifts.shift_understaffed_mail",
                            "Schicht mit Personalmangel",
                        )
                    ],
                    max_length=128,
                ),
                blank=True,
                default=tapir.core.tapir_email_base.get_all_emails,
                size=None,
            ),
        ),
    ]