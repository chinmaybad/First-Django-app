# Generated by Django 2.1.5 on 2019-02-12 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_auto_20190212_1425'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicators',
            name='value',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]