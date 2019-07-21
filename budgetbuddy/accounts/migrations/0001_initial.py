# Generated by Django 2.2.3 on 2019-07-13 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccountType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_type', models.CharField(choices=[('Savings', 'Savings'), ('Expenses', 'Expenses'), ('Flex', 'Flex')], max_length=20)),
                ('is_cash_account', models.BooleanField()),
            ],
        ),
    ]