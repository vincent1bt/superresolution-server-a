# Generated by Django 3.2.10 on 2022-01-03 23:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_rename_zip_ip_srtask_zip_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='srspotserver',
            name='ip',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
