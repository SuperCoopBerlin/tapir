# Generated by Django 5.1.1 on 2024-10-18 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shifts", "0061_shift_flexible_time_shiftattendance_custom_time_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shift",
            name="end_time",
            field=models.DateTimeField(
                help_text="If 'flexible time' is enabled, then the time component is ignored"
            ),
        ),
        migrations.AlterField(
            model_name="shift",
            name="start_time",
            field=models.DateTimeField(
                help_text="If 'flexible time' is enabled, then the time component is ignored"
            ),
        ),
        migrations.AlterField(
            model_name="shiftattendancetemplate",
            name="custom_time",
            field=models.TimeField(
                help_text="This shift lets you choose at what time you come during the day of the shift. In order to help organising the attendance, please specify when you expect to come.Setting or updating this field will set the time for all individual shifts generated from this ABCD shift.You can update the time of a single shift individually and at any time on the shift page.",
                null=True,
                verbose_name="Chosen time",
            ),
        ),
    ]