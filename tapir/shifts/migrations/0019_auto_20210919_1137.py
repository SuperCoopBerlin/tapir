# Generated by Django 3.1.13 on 2021-09-19 09:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shifts", "0018_shiftattendancetakenoverlogentry"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="shiftattendance",
            index=models.Index(fields=["slot"], name="shifts_shif_slot_id_0bc247_idx"),
        ),
    ]
