# Generated by Django 2.2.3 on 2019-07-13 06:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20190713_0248'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('contribution_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('month_intervals', models.IntegerField()),
                ('active', models.BooleanField(default=True)),
                ('account_type_id', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.AccountType')),
            ],
        ),
    ]
