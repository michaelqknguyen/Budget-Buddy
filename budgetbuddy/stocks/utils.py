from budgetbuddy.accounts.models import BudgetAccount, MoneyAccount
from budgetbuddy.stocks.models import Stock, StockShares

from django.db.models import Sum, F


def get_stock_shares(user, stock=None, active_account=None, account_type=None):
    if account_type is MoneyAccount:
        return StockShares.objects.filter(user=user, brokerage_account=active_account)
    elif account_type is BudgetAccount:
        return StockShares.objects.filter(user=user, budget_account=active_account)
    else:
        return StockShares.objects.filter(user=user)


def calculate_investment_balance(shares: StockShares):
    total_balance = 0
    if not shares:
        return total_balance

    Stock.objects.update_market_prices()
    total = shares.aggregate(total=Sum(F('num_shares') * F('stock__market_price')))['total']

    # for share in shares:
    #     total_balance += float(share.num_shares) * float(share.stock.market_price)

    if total is None:
        return 0

    return round(total, 2)
