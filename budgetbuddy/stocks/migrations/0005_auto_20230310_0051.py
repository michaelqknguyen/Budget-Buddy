# Generated by Django 2.2.3 on 2023-03-10 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0004_auto_20210223_1908'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stocktransaction',
            name='price',
            field=models.DecimalField(decimal_places=4, max_digits=10),
        ),
    ]