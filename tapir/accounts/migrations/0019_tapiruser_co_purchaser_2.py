# Generated by Django 5.1.5 on 2025-06-24 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0018_alter_optionalmails_mail_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="tapiruser",
            name="co_purchaser_2",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="Second co-Purchaser"
            ),
        ),
    ]
