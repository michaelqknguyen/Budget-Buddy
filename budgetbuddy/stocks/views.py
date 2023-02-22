import copy
import logging
import re
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse
from budgetbuddy.accounts.models import MoneyAccount, BudgetAccount, Transaction
from budgetbuddy.accounts.views import account_page_reverse
from budgetbuddy.accounts.utils import ensure_user_access
from budgetbuddy.stocks.forms import StockTransactionForm
from budgetbuddy.stocks.models import Stock, StockShares, StockTransaction


# TODO: finish
@login_required
def create_stock_transaction(request):
    if request.method == 'POST':
        money_or_budget = request.POST.get('money_or_budget')
        money_account_id = request.POST.get('brokerage_account')
        budget_account_id = request.POST.get('budget_account')
        brokerage_account_object = get_object_or_404(MoneyAccount, pk=money_account_id, user=request.user)
        budget_account_object = get_object_or_404(BudgetAccount, pk=budget_account_id, user=request.user)
        ticker = request.POST.get('ticker')
        stock, was_created = Stock.objects.get_or_create(ticker=ticker)

        if was_created:
            Stock.objects.update_market_prices(update_interval=0)

        ensure_user_access(model=MoneyAccount, pk=money_account_id, user=request.user)
        ensure_user_access(model=BudgetAccount, pk=budget_account_id, user=request.user)

        stock_shares = StockShares.objects.get_or_create(
            user=request.user,
            stock=stock,
            brokerage_account=brokerage_account_object,
            budget_account=budget_account_object,
        )[0]

        # add user to post items
        form_data = copy.copy(request.POST)
        form_data['shares'] = stock_shares.id
        stock_transaction = StockTransactionForm(form_data)
        if stock_transaction.is_valid():
            # Create monetary transaction for stock transaction
            num_shares = request.POST.get('num_shares')
            transaction_str = "{} {} shares".format(num_shares, ticker)
            transaction_amount = round(
                float(num_shares) * float(request.POST.get('price')), 2)
            if request.POST.get('transaction_type') == 'B':
                # spending money if a purchase
                transaction_str = 'Buy ' + transaction_str
                transaction_amount = -1 * transaction_amount
                stock_shares.num_shares = float(stock_shares.num_shares) + float(num_shares)
            else:
                transaction_str = 'Sell ' + transaction_str
                stock_shares.num_shares = float(stock_shares.num_shares) - float(num_shares)
            transaction = Transaction(
                notes="Stock Transaction",
                description=transaction_str,
                transaction_date=request.POST.get('transaction_date'),
                amount_spent=transaction_amount,
                user=request.user,
                money_account=brokerage_account_object,
                budget_account=budget_account_object,
            )

            transaction.save()
            stock_transaction.save()
            stock_shares.save(update_fields=['num_shares'])
            messages.success(request, '{} transaction has been added'.format(request.POST['ticker']))
        else:
            logging.warning(stock_transaction.errors)
            messages.error(request, "Error creating transaction")

        if money_or_budget == 'm':
            return account_page_reverse(money_or_budget, money_account_id)
        return account_page_reverse(money_or_budget, budget_account_id)  # handles budget and null


class StockTransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = StockTransaction
    form_class = StockTransactionForm
    template_name = 'stocks/transaction_form.html'
    money_or_budget = None

    def test_func(self):
        path = self.request.path
        transaction_id = re.search('trans/(.*)/edit', path).group(1)
        return StockTransaction.objects.filter(pk=transaction_id, user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "{} transaction successfully updated".format(self.object.shares))
        if self.money_or_budget == 'm':
            return reverse('budget:money_account', args=[self.object.shares.brokerage_account.id])
        elif self.money_or_budget == 'b':
            return reverse('budget:budget_account', args=[self.object.shares.budget_account.id])
        else:
            return reverse('budget:all_accounts')
            pass


class StockTransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = StockTransaction
    money_or_budget = None

    def test_func(self):
        path = self.request.path
        transaction_id = re.search('trans/(.*)/delete', path).group(1)
        return StockTransaction.objects.filter(pk=transaction_id, user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "{} transaction successfully deleted".format(self.object.shares))
        if self.money_or_budget == 'm':
            return reverse('budget:money_account', args=[self.object.shares.brokerage_account.id])
        elif self.money_or_budget == 'b':
            return reverse('budget:budget_account', args=[self.object.shares.budget_account.id])
        else:
            return reverse('budget:all_accounts')
            pass
