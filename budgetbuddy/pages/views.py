from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
from django.urls import reverse
from accounts.models import MoneyAccount, BudgetAccount


def index(request):
    user = request.user

    money_balance = (
        MoneyAccount.
        objects.
        filter(
            active=True,
            user=user
        )
        .annotate(total=Coalesce(Sum(F('transaction__amount_spent')), 0))
        .aggregate(money_total=Coalesce(Sum('total'), 0))
    ).get('money_total')

    budget_balance = (
        BudgetAccount.
        objects.
        filter(
            active=True,
            user=user
        )
        .annotate(total=Coalesce(Sum(F('transaction__amount_spent')), 0))
        .aggregate(balance_total=Coalesce(Sum('total'), 0))
    ).get('balance_total')

    if money_balance != budget_balance:
        messages.warning(request, 'Your money accounts and budget accounts are not balanced')

    context = {
        'money_balance': money_balance,
        'budget_balance': budget_balance,
    }

    return render(request, 'pages/home.html', context)
