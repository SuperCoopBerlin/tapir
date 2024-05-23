# Generated by Django 3.2.23 on 2024-05-22 17:50

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0049_auto_20240515_1331'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shareownership',
            name='cancellation_date',
        ),
        migrations.AlterField(
            model_name='resignedmembership',
            name='cancellation_date',
            field=models.DateField(blank=True, default=datetime.datetime(2024, 5, 22, 17, 50, 26, 744464, tzinfo=utc), null=True),
        ),
    ]