# Generated by Django 2.2.3 on 2019-07-19 20:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_auto_20190716_1909'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetaccount',
            name='account_type',
            field=models.ForeignKey(limit_choices_to={'is_cash_account': False}, on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.AccountType'),
        ),
        migrations.AlterField(
            model_name='moneyaccount',
            name='account_type',
            field=models.ForeignKey(limit_choices_to={'is_cash_account': True}, on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.AccountType'),
        ),
    ]
