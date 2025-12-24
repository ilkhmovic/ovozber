from django.db import migrations, models


def set_poll_from_district(apps, schema_editor):
    Candidate = apps.get_model('api', 'Candidate')
    for c in Candidate.objects.all():
        if c.district_id and not c.poll_id:
            c.poll_id = c.district.region.poll_id
            c.save(update_fields=['poll_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_poll_remove_telegramuser_has_voted_alter_region_name_and_more'),
    ]

    operations = [
        # Add poll field nullable first
        migrations.AddField(
            model_name='candidate',
            name='poll',
            field=models.ForeignKey(null=True, on_delete=models.CASCADE, related_name='candidates', to='api.poll', verbose_name="So'rovnoma"),
        ),
        # Allow district to be nullable
        migrations.AlterField(
            model_name='candidate',
            name='district',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='candidates', to='api.district', verbose_name='Tuman'),
        ),
        # Populate poll from district -> region -> poll
        migrations.RunPython(set_poll_from_district, reverse_code=migrations.RunPython.noop),
        # Make poll non-nullable
        migrations.AlterField(
            model_name='candidate',
            name='poll',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='candidates', to='api.poll', verbose_name="So'rovnoma"),
        ),
    ]
