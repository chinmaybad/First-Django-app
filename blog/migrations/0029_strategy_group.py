# Generated by Django 2.1.5 on 2019-03-15 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0028_intraday_momentum_index'),
    ]

    operations = [
        migrations.CreateModel(
            name='Strategy_Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('exp', models.CharField(default='True', max_length=200)),
            ],
        ),
    ]
