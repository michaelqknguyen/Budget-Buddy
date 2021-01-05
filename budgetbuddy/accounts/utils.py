import datetime
import math

from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from budgetbuddy.accounts.models import Transaction, BudgetAccount, MoneyAccount


def subtract_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month later.

    Note that the resultant day of the month might change if the following
    month has fewer days:

        >>> subtract_one_month(datetime.date(2010, 3, 31))
        datetime.date(2010, 2, 28)
    """
    one_day = datetime.timedelta(days=1)
    one_month_earlier = t - one_day
    while one_month_earlier.month == t.month or one_month_earlier.day > t.day:
        one_month_earlier -= one_day
    return one_month_earlier


def get_date_range(request):
    if 'end_date' in request.GET:
        end_date = parse_date(request.GET.get('end_date'))
    else:
        end_date = datetime.date.today()
    if 'start_date' in request.GET:
        start_date = parse_date(request.GET.get('start_date'))
    else:
        start_date = subtract_one_month(end_date)

    return start_date, end_date


def get_transactions(user, active_account=None, account_type=None):
    if account_type is MoneyAccount:
        return Transaction.objects.filter(user=user, money_account=active_account)
    elif account_type is BudgetAccount:
        return Transaction.objects.filter(user=user, budget_account=active_account)
    else:
        return Transaction.objects.filter(user=user)


def round_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier


def ensure_user_access(model: models.Model, pk: int, user):
    """ensure user has access to specified model"""
    if model is None:
        return None
    return get_object_or_404(model, pk=pk, user=user)
