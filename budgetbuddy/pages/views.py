from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Q, DecimalField
from django.db.models.functions import Coalesce
from django.urls import reverse
from budgetbuddy.accounts.models import MoneyAccount, BudgetAccount
from budgetbuddy.stocks.models import StockShares


@login_required
def index(request):
    user = request.user
    if user.is_anonymous:
        return HttpResponseRedirect(reverse('account_login'))

    money_balance = (
        MoneyAccount.
        objects.
        filter(
            active=True,
            user=user
        )
        .annotate(total=Coalesce(Sum(F('transaction__amount_spent'), output_field=DecimalField()), 0))
        .aggregate(money_total=Coalesce(Sum('total'), 0))
    ).get('money_total')

    budget_balance = (
        BudgetAccount.
        objects.
        filter(
            active=True,
            user=user
        )
        .annotate(total=Coalesce(Sum(F('transaction__amount_spent'), output_field=DecimalField()), 0))
        .aggregate(balance_total=Coalesce(Sum('total'), 0))
    ).get('balance_total')

    investment_balance = StockShares.objects.investment_sum(user)

    try:
        flex_account = (
            BudgetAccount
            .objects
            .annotate(total=Coalesce(Sum(F('transaction__amount_spent'), output_field=DecimalField()), 0))
            .get(
                Q(account_type__account_type='Flex'),
                user=user,
            )
        )
    except BudgetAccount.DoesNotExist:
        flex_account = None

    if not flex_account:
        messages.error(request, 'A Flex budget account is required to be created')

    if money_balance != budget_balance:
        messages.warning(request, 'Your money accounts and budget accounts are not balanced')

    context = {
        'money_balance': money_balance,
        'budget_balance': budget_balance,
        'investment_balance': investment_balance,
    }

    return render(request, 'pages/home.html', context)
