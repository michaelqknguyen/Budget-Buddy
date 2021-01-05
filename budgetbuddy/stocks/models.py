from django.conf import settings
from django.db import models

from budgetbuddy.accounts.models import MoneyAccount, BudgetAccount
from budgetbuddy.stocks.managers import StockManager, StockSharesManager


class Stock(models.Model):
    ticker = models.CharField(max_length=8, primary_key=True)
    asset_class = models.CharField(max_length=200, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    market_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    objects = StockManager()

    def __str__(self):
        return self.ticker

    # @property
    # def market_price(self):
    #     return get_stock_price(self.ticker)


class StockShares(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    stock = models.ForeignKey(Stock, on_delete=models.DO_NOTHING, related_name='shares')
    brokerage_account = models.ForeignKey(MoneyAccount, null=True, blank=True,
                                          on_delete=models.DO_NOTHING,
                                          limit_choices_to={'is_brokerage': True})
    budget_account = models.ForeignKey(BudgetAccount, null=True, blank=True,
                                       on_delete=models.DO_NOTHING)

    # objects = StockSharesManager()

    num_shares = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    @property
    def shares_value(self):
        return self.num_shares * self.stock.market_price

    # @property
    # def num_shares_owned(self):
    #     total_bought = self.transactions.filter(
    #         transaction_type='B').aggregate(total=Sum('num_shares')).get('total') or 0
    #     total_sold = self.transactions.filter(
    #         transaction_type='S').aggregate(total=Sum('num_shares')).get('total') or 0
    #     return total_bought - total_sold

    # @property
    # def num_shares_sold(self):
    #     return self.transactions.filter(transaction_type='S').aggregate(total=Sum('num_shares')).get('total') or 0

    # # return if more shares sold then bought -- something is wrong
    # @property
    # def more_shares_sold(self):
    #     return (self.num_shares_sold - self.num_shares_owned) > 0

    def __str__(self):
        return '{}_{}_{}'.format(self.stock, self.brokerage_account, self.budget_account)


class StockTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    BUY = 'B'
    SELL = 'S'
    TRANSACTION_CHOICES = [
        (BUY, 'Buy'),
        (SELL, 'Sell'),
    ]

    shares = models.ForeignKey(StockShares, on_delete=models.DO_NOTHING, related_name='transactions')
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=2, choices=TRANSACTION_CHOICES)
    num_shares = models.DecimalField(max_digits=20, decimal_places=4)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def transactional_value(self):
        # buying shares would be negative money from cash balance
        shares_value = self.num_shares * self.price
        if self.transaction_type == self.BUY:
            return -1 * shares_value

        return shares_value
