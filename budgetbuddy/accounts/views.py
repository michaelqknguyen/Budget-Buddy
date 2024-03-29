import operator
import re
import datetime
import json
from itertools import chain
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse
from budgetbuddy.accounts.models import MoneyAccount, BudgetAccount, Transaction
from budgetbuddy.accounts.forms import BudgetAccountForm, TransactionForm, MoneyAccountForm
from budgetbuddy.accounts.utils import get_transactions, get_date_range, ensure_user_access
from budgetbuddy.stocks.forms import StockTransactionForm
from budgetbuddy.stocks.models import StockTransaction
from budgetbuddy.stocks.utils import get_stock_shares, calculate_investment_balance


@login_required
def index(request):
    user = request.user

    # for the active checkbox, it contains the value of the other checkbox
    budget_active = True
    money_active = True
    if 'moneyActive' in request.GET:
        budget_active = request.GET.get('moneyActive')
        money_active = False
    # money_active = request.GET.get('budgetActive') or True
    if 'budgetActive' in request.GET:
        money_active = request.GET.get('budgetActive')
        budget_active = False
    # budget_active = request.GET.get('moneyActive') or True

    # always show all actives
    money_accounts = (
        MoneyAccount.
        objects.
        filter(
            active__in=(True, money_active),
            user=user
        )
        .annotate(total=Coalesce(Sum(F('transaction__amount_spent')), Decimal(0)))
        .order_by('name')
    )
    # redirect to moeny account creation if no money account
    # if not money_accounts:
    #     return HttpResponseRedirect(reverse('money_account_create'))

    try:
        flex_account = (
            BudgetAccount
            .objects
            .annotate(total=Coalesce(Sum(F('transaction__amount_spent')), Decimal(0)))
            .get(
                Q(account_type__account_type='Flex'),
                user=user,
            )
        )
    except BudgetAccount.DoesNotExist:
        flex_account = None

    budget_accounts = (
        BudgetAccount.
        objects.
        filter(
            active__in=(True, budget_active),
            user=user)
        .exclude(Q(account_type__account_type='Flex'))
        .annotate(total=Coalesce(Sum(F('transaction__amount_spent')), Decimal(0)))
        .order_by('name')
    )

    context = {
        'maccounts': money_accounts,
        'money_active_only': money_active,
        'flex_account': flex_account,
        'budget_accounts': budget_accounts,
        'budget_active_only': budget_active,
    }
    return render(request, 'accounts/accounts.html', context)


@login_required
def money_account(request, account_id):
    return account_view(request, account_id, MoneyAccount)


@login_required
def budget_account(request, account_id):
    return account_view(request, account_id, BudgetAccount)


@login_required
def all_accounts(request):
    return account_view(request, None, None)


@login_required
def account_view(request, account_id, account_type):
    user = request.user

    if account_id:
        # focusing on transaction page on one account
        active_account = get_object_or_404(account_type, pk=account_id, user=user)
    else:
        # showing for all accounts
        active_account = None

    money_accounts = MoneyAccount.objects.filter(active=True, user=user).order_by('name')
    budget_accounts = BudgetAccount.objects.filter(active=True, user=user).order_by('name')

    # context for template what each account is since they will be blended together
    # sort the accounts in a list by abc order
    accounts = sorted(chain(money_accounts, budget_accounts),
                      key=operator.attrgetter('name'))

    # get dates for transaction time frame
    start_date, end_date = get_date_range(request)

    # get transactions for this account
    all_transactions = get_transactions(user, active_account, account_type)
    all_stock_shares = get_stock_shares(user, active_account=active_account, account_type=account_type)
    all_stock_shares = all_stock_shares.prefetch_related('brokerage_account', 'budget_account')
    # all_stock_transactions = StockTransaction.objects.filter(shares__in=all_stock_shares)
    if account_id:
        balance = all_transactions.aggregate(
            balance=Coalesce(Sum('amount_spent'), Decimal(0))).get('balance', Decimal(0))
    else:
        # only consider actual money account balances for balance calc for all account view
        balance = (
            all_transactions
            .filter(money_account__isnull=False)
            .aggregate(
                balance=Coalesce(Sum('amount_spent'), Decimal(0)))
            .get('balance', 0)
        )
    subset_transactions = all_transactions.filter(transaction_date__range=(start_date, end_date))
    # subset_stock_transactions = all_stock_transactions.filter(transaction_date__range=(start_date, end_date))
    subset_stock_transactions = (
        StockTransaction
        .objects
        .filter(shares__in=all_stock_shares, transaction_date__range=(start_date, end_date))
        .select_related('shares')
    )
    # exclude paycheck contributions from the "spent" calculation
    subset_spent = (
        subset_transactions
        .filter(paystub__isnull=True)
        .aggregate(
            spent=Coalesce(Sum('amount_spent'), Decimal(0)))
        .get('spent', 0)
    )

    # initialize transaction form
    initial_transaction = {
        'transaction_date': datetime.date.today(),
    }
    if account_type is MoneyAccount:
        initial_transaction['money_account'] = active_account
    elif account_type is BudgetAccount:
        initial_transaction['budget_account'] = active_account
    # else:
    #     money_or_budget = None
    # transaction_form = TransactionForm(initial=initial_transaction)

    # calculate all the money spent or made selling or buying stock
    # these are the "realized gains"
    stock_realized = (
        all_transactions
        .filter(
            (
                Q(description__contains='shares')
                & (
                    Q(description__contains='Buy') |
                    Q(description__contains='Sell')
                )
            )
            | Q(description__contains='BTO')
            | Q(description__contains='STO')
            | Q(description__contains='BTC')
            | Q(description__contains='STC')
        )
        .aggregate(
            spent=Coalesce(Sum('amount_spent'), Decimal(0)))
        .get('spent', 0)
    )
    # get the current investment balance minus the amount spent on stocks thus far
    investment_balance = calculate_investment_balance(all_stock_shares)
    potential_gain = stock_realized + investment_balance

    context = {
        'active_account': active_account,
        'money_accounts': money_accounts,
        'budget_accounts': budget_accounts,
        'accounts': accounts,
        'transactions': subset_transactions,
        'stock_shares': all_stock_shares,
        'stock_transactions': subset_stock_transactions,
        'start_date': start_date,
        'end_date': end_date,
        'balance': balance,
        'investment_balance': calculate_investment_balance(all_stock_shares),
        'time_frame_spent': subset_spent,
        'transaction_form': initial_transaction,
        'stock_gains': potential_gain,
    }
    return render(request, 'accounts/account.html', context)


def account_page_reverse(money_or_budget, account_id):
    # logic to return to page that came from for money/budget or all accounts
    # redirect to the correct page based on where we started
    if money_or_budget == 'm':
        return HttpResponseRedirect(reverse('budget:money_account', args=[account_id]))
    elif money_or_budget == 'b':
        return HttpResponseRedirect(reverse('budget:budget_account', args=[account_id]))
    else:
        return HttpResponseRedirect(reverse('budget:all_accounts'))


@login_required
def create_transaction(request):
    if request.method == 'POST':
        money_or_budget = request.POST.get('money_or_budget')

        money_account_id = request.POST.get('money_account')
        budget_account_id = request.POST.get('budget_account')
        # # double check to make sure user has access to both accounts
        if money_account_id:
            get_object_or_404(MoneyAccount, pk=money_account_id, user=request.user)
        if budget_account_id:
            get_object_or_404(BudgetAccount, pk=budget_account_id, user=request.user)

        # add user to post items
        transaction = TransactionForm(request.POST)
        if transaction.is_valid():
            transaction.save()
            messages.success(request, '{} transaction has been added'.format(request.POST['description']))
        else:
            messages.error(request, "Error creating transaction")

        if money_or_budget == 'm':
            return account_page_reverse(money_or_budget, money_account_id)
        return account_page_reverse(money_or_budget, budget_account_id)  # handles budget and null


@login_required
def transfer_transaction(request):
    if request.method == 'POST':
        # account json format should have account_id and money_or_budget
        from_account = json.loads(request.POST['fromAccount'])
        to_account = json.loads(request.POST['toAccount'])
        from_account_id = from_account['account_id']
        to_account_id = to_account['account_id']

        money_or_budget = request.POST.get('money_or_budget')
        return_url = account_page_reverse(money_or_budget, from_account_id)

        if from_account['money_or_budget'] != to_account['money_or_budget']:
            messages.error(request, 'Transfers can only be made between two budget accounts or two money accounts')
            return return_url
        elif from_account['money_or_budget'] == 'm':
            account_type = MoneyAccount
        elif from_account['money_or_budget'] == 'b':
            account_type = BudgetAccount

        transaction_date = request.POST['transaction_date']
        amount_transfer = float(request.POST['amount_spent'])

        # initialize transaction for the from and to accounts
        from_trans = Transaction(
            notes="Transfer",
            transaction_date=transaction_date,
            amount_spent=-amount_transfer,
            user=request.user,
        )
        to_trans = Transaction(
            notes="Transfer",
            transaction_date=transaction_date,
            amount_spent=amount_transfer,
            user=request.user,
        )

        from_account_object = get_object_or_404(account_type, pk=from_account_id, user=request.user)
        to_account_object = get_object_or_404(account_type, pk=to_account_id, user=request.user)
        from_trans.description = "To {}".format(to_account_object)
        to_trans.description = "From {}".format(from_account_object)

        if from_account['money_or_budget'] == 'm':
            from_trans.money_account = from_account_object
            to_trans.money_account = to_account_object
        elif from_account['money_or_budget'] == 'b':
            from_trans.budget_account = from_account_object
            to_trans.budget_account = to_account_object

        from_trans.save()
        to_trans.save()
        messages.success(request, 'Transferred ${:.2f} from {} to {}'.format(amount_transfer, from_account_object, to_account_object))
        return return_url


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template = 'accounts/transaction_form.html'
    money_or_budget = None

    def test_func(self):
        path = self.request.path
        transaction_id = re.search('trans/(.*)/edit', path).group(1)
        return Transaction.objects.filter(pk=transaction_id, user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "{} transaction successfully updated".format(self.object.description))
        if self.money_or_budget == 'm':
            return reverse('budget:money_account', args=[self.object.money_account.id])
        elif self.money_or_budget == 'b':
            return reverse('budget:budget_account', args=[self.object.budget_account.id])
        else:
            return reverse('budget:all_accounts')
            pass


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    money_or_budget = None

    def test_func(self):
        path = self.request.path
        transaction_id = re.search('trans/(.*)/delete', path).group(1)
        return Transaction.objects.filter(pk=transaction_id, user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "{} transaction successfully deleted".format(self.object.description))
        if self.money_or_budget == 'm':
            return reverse('budget:money_account', args=[self.object.money_account.id])
        elif self.money_or_budget == 'b':
            return reverse('budget:budget_account', args=[self.object.budget_account.id])
        else:
            return reverse('budget:all_accounts')
            pass


class BudgetAccountCreateView(LoginRequiredMixin, CreateView):
    model = BudgetAccount
    form_class = BudgetAccountForm
    template_name = 'accounts/account_form.html'

    def get_initial(self, *args, **kwargs):
        initial = super(BudgetAccountCreateView, self).get_initial(**kwargs)
        initial['user'] = self.request.user
        return initial

    def get_success_url(self):
        return reverse('budget:budget')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Budget Account'
        return context


class BudgetAccountUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BudgetAccount
    form_class = BudgetAccountForm
    template_name = 'accounts/account_form.html'

    def test_func(self):
        path = self.request.path
        account_id = re.search('b/(.*)/edit', path).group(1)
        return BudgetAccount.objects.filter(pk=account_id, user=self.request.user)

    def get_success_url(self):
        return reverse('budget:budget')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit {} Account'.format(self.object.name)
        return context


class MoneyAccountCreateView(LoginRequiredMixin, CreateView):
    model = MoneyAccount
    form_class = MoneyAccountForm
    template_name = 'accounts/account_form.html'

    def get_initial(self, *args, **kwargs):
        initial = super(MoneyAccountCreateView, self).get_initial(**kwargs)
        initial['user'] = self.request.user
        initial['date_opened'] = datetime.date.today()
        return initial

    def get_success_url(self):
        return reverse('budget:budget')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Money Account'
        return context


class MoneyAccountUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = MoneyAccount
    form_class = MoneyAccountForm
    template_name = 'accounts/account_form.html'

    def test_func(self):
        path = self.request.path
        account_id = re.search('m/(.*)/edit', path).group(1)
        return MoneyAccount.objects.filter(pk=account_id, user=self.request.user)

    def get_success_url(self):
        return reverse('budget:budget')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit {} Account'.format(self.object.name)
        return context
