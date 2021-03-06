# Generated by Django 3.2.10 on 2022-01-03 22:24

from django.db import migrations

def create_default_srspot_model(apps, schema_editor):
    # We can't import the SRSpotServer model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    SRSpotServer = apps.get_model('tasks', 'SRSpotServer')

    SRSpotServer.objects.create(status="OFF")

class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_srspot_model),
    ]
