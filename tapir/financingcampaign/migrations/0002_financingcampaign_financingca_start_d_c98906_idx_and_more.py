# Generated by Django 5.1.2 on 2024-11-08 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("financingcampaign", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="financingcampaign",
            index=models.Index(
                fields=["start_date"], name="financingca_start_d_c98906_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="financingcampaign",
            index=models.Index(
                fields=["end_date"], name="financingca_end_dat_7283d6_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="financingcampaign",
            index=models.Index(
                fields=["start_date", "end_date"], name="financingca_start_d_594d91_idx"
            ),
        ),
    ]