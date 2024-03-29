# Generated by Django 3.2.21 on 2023-10-21 19:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("shifts", "0047_alter_shifttemplate_start_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="createshiftattendancelogentry",
            name="shift",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="shifts.shift"
            ),
        ),
        migrations.AlterField(
            model_name="createshiftattendancetemplatelogentry",
            name="shift_template",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="shifts.shifttemplate"
            ),
        ),
        migrations.AlterField(
            model_name="deleteshiftattendancetemplatelogentry",
            name="shift_template",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="shifts.shifttemplate"
            ),
        ),
        migrations.AlterField(
            model_name="shift",
            name="shift_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="generated_shifts",
                to="shifts.shifttemplate",
            ),
        ),
        migrations.AlterField(
            model_name="shiftaccountentry",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="shift_account_entries",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="shiftattendance",
            name="account_entry",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="shift_attendance",
                to="shifts.shiftaccountentry",
            ),
        ),
        migrations.AlterField(
            model_name="shiftattendance",
            name="slot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attendances",
                to="shifts.shiftslot",
            ),
        ),
        migrations.AlterField(
            model_name="shiftattendance",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="shift_attendances",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="shiftattendancetakenoverlogentry",
            name="shift",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="shifts.shift"
            ),
        ),
        migrations.AlterField(
            model_name="shiftattendancetemplate",
            name="slot_template",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attendance_template",
                to="shifts.shiftslottemplate",
            ),
        ),
        migrations.AlterField(
            model_name="shiftattendancetemplate",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="shift_attendance_templates",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="shiftcycleentry",
            name="shift_account_entry",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="shift_cycle_log",
                to="shifts.shiftaccountentry",
            ),
        ),
        migrations.AlterField(
            model_name="shiftslot",
            name="slot_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="generated_slots",
                to="shifts.shiftslottemplate",
            ),
        ),
        migrations.AlterField(
            model_name="shiftuserdata",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="shift_user_data",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="updateshiftattendancestatelogentry",
            name="shift",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="shifts.shift"
            ),
        ),
    ]
