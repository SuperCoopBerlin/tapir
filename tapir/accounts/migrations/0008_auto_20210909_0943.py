# Generated by Django 3.1.13 on 2021-09-09 07:43

import django.contrib.postgres.fields.hstore
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("log", "0003_textlogentry"),
        ("accounts", "0007_auto_20210903_1609"),
    ]

    operations = [
        migrations.CreateModel(
            name="UpdateTapirUserLogEntry",
            fields=[
                (
                    "logentry_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="log.logentry",
                    ),
                ),
                ("old_values", django.contrib.postgres.fields.hstore.HStoreField()),
                ("new_values", django.contrib.postgres.fields.hstore.HStoreField()),
            ],
            options={
                "abstract": False,
            },
            bases=("log.logentry",),
        ),
    ]
