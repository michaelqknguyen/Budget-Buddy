# Generated by Django 2.2.3 on 2020-02-18 19:24

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('paychecks', '0004_assigned_budget_paycheck'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deduction',
            name='creation_date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2020, 2, 18, 19, 24, 13, 784694, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='paycheck',
            name='creation_date',
            field=models.DateField(blank=True, default=datetime.datetime(2020, 2, 18, 19, 24, 13, 783406, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='paystub',
            name='creation_date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2020, 2, 18, 19, 24, 13, 785453, tzinfo=utc)),
        ),
    ]
