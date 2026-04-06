from django.db.models import F, Sum

from budgetbuddy.accounts.models import BudgetAccount, MoneyAccount
from budgetbuddy.stocks.models import StockShares


def get_stock_shares(user, stock=None, active_account=None, account_type=None):
    if account_type is MoneyAccount:
        return StockShares.objects.filter(user=user, brokerage_account=active_account)
    elif account_type is BudgetAccount:
        return StockShares.objects.filter(user=user, budget_account=active_account)
    else:
        return StockShares.objects.filter(user=user)


def calculate_investment_balance(shares: StockShares):
    """Calculate the total investment balance from share holdings.

    Pure read function -- only aggregates values already in the database.
    Does NOT trigger external API calls or price updates.
    """
    if not shares:
        return 0

    total = shares.aggregate(total=Sum(F("num_shares") * F("stock__market_price")))[  # type: ignore[attr-defined]
        "total"
    ]

    if total is None:
        return 0

    return round(total, 2)
