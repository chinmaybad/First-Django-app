# Generated by Django 2.1.5 on 2019-03-07 10:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0024_auto_20190305_1323'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bollinger_Band',
            fields=[
                ('indicator_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='blog.Indicator')),
                ('period', models.CharField(default='14', max_length=100)),
                ('standard_deviation', models.CharField(default='2', max_length=100)),
                ('field', models.CharField(default='close', max_length=100)),
                ('interval', models.CharField(default='minute', max_length=100)),
                ('band_type', models.CharField(default='minute', max_length=100)),
            ],
            bases=('blog.indicator',),
        ),
    ]
