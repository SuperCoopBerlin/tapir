# Generated by Django 3.1.13 on 2021-10-15 07:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coop", "0019_auto_20211015_0910"),
    ]

    operations = [
        migrations.AlterField(
            model_name="draftuser",
            name="num_shares",
            field=models.IntegerField(default=1, verbose_name="Number of Shares"),
        ),
    ]
