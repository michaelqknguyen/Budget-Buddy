# Generated by Django 2.2.3 on 2019-07-16 23:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_auto_20190715_2134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='moneyaccount',
            name='contribution_amount',
        ),
        migrations.RemoveField(
            model_name='moneyaccount',
            name='month_intervals',
        ),
    ]