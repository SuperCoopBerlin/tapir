# Generated by Django 3.2.11 on 2022-02-08 20:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coop", "0024_auto_20220206_1040"),
    ]

    operations = [
        migrations.AddField(
            model_name="draftuser",
            name="paid_shares",
            field=models.BooleanField(default=False, verbose_name="Paid Shares"),
        ),
    ]
