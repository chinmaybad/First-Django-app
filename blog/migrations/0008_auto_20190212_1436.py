# Generated by Django 2.1.5 on 2019-02-12 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_auto_20190212_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicators',
            name='value',
            field=models.FloatField(blank=True, default='0', null=True),
        ),
    ]