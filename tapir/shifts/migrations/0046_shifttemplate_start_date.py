# Generated by Django 3.2.20 on 2023-08-15 10:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shifts", "0045_auto_20230808_1242"),
    ]

    operations = [
        migrations.AddField(
            model_name="shifttemplate",
            name="start_date",
            field=models.DateField(
                help_text="This determines from which date shifts should be generated from this ABCD shift.",
                null=True,
            ),
        ),
    ]
