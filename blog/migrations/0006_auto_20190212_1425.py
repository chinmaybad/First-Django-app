# Generated by Django 2.1.5 on 2019-02-12 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_indicators_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicators',
            name='value',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
    ]
