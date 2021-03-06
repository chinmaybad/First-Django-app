# Generated by Django 2.1.5 on 2019-03-12 10:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0026_auto_20190312_1253'),
    ]

    operations = [
        migrations.CreateModel(
            name='High_Low',
            fields=[
                ('indicator_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='blog.Indicator')),
                ('interval', models.CharField(default='minute', max_length=100)),
            ],
            bases=('blog.indicator',),
        ),
        migrations.CreateModel(
            name='Price_Momentum_Oscillator',
            fields=[
                ('indicator_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='blog.Indicator')),
                ('field', models.CharField(default='close', max_length=100)),
                ('interval', models.CharField(default='minute', max_length=100)),
                ('smoothing_period', models.CharField(default='35', max_length=100)),
                ('double_smoothing_period', models.CharField(default='20', max_length=100)),
                ('signal_period', models.CharField(default='10', max_length=100)),
                ('PMO_type', models.CharField(default='PMO', max_length=100)),
            ],
            bases=('blog.indicator',),
        ),
    ]
