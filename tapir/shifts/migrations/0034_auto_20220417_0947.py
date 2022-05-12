# Generated by Django 3.2.12 on 2022-04-17 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shifts", "0033_shiftslottemplate_warnings"),
    ]

    operations = [
        migrations.AddField(
            model_name="shift",
            name="cancelled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="shift",
            name="cancelled_reason",
            field=models.CharField(max_length=1000, null=True),
        ),
    ]