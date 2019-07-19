from django.db import models
from django.conf import settings
from datetime import datetime
from paychecks.models import Paystub


class AccountType(models.Model):
    account_type = models.CharField(max_length=20)
    is_cash_account = models.BooleanField()

    def __str__(self):
        return self.account_type


class Account(models.Model):
    name = models.CharField(max_length=200)
    account_type = models.ForeignKey(AccountType, on_delete=models.DO_NOTHING)
    active = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class MoneyAccount(Account):
    date_opened = models.DateField(default=datetime.now)
    date_closed = models.DateField(null=True, blank=True)


class BudgetAccount(Account):
    contribution_amount = models.DecimalField(max_digits=8, decimal_places=2)
    month_intervals = models.IntegerField()


class Transaction(models.Model):
    description = models.CharField(max_length=200)
    notes = models.TextField(null=True, blank=True)
    transaction_date = models.DateField()
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2)
    money_account = models.ForeignKey(MoneyAccount, null=True, blank=True,
                                         on_delete=models.DO_NOTHING)
    budget_account = models.ForeignKey(BudgetAccount, null=True, blank=True,
                                          on_delete=models.DO_NOTHING)
    paystub = models.ForeignKey(Paystub, null=True, blank=True,
                                   on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
