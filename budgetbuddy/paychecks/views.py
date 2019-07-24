from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect
from budgetbuddy.paychecks.models import Paycheck, PayType, Deduction, Paystub
from budgetbuddy.paychecks.forms import DeductionForm, PaystubForm, TransactionPaystubForm, PaycheckForm
from budgetbuddy.accounts.models import Transaction, BudgetAccount, MoneyAccount
import re
import datetime


def index(request, paycheck_id=None):
    user = request.user
    paychecks = Paycheck.objects.filter(active=True, user=user)
    if not paychecks:
        # redirect to create page if no paychecks
        return HttpResponseRedirect(reverse('paycheck_create'))

    # if form get, get the requested paycheck_id
    if 'paycheck_id' in request.GET:
        paycheck_id = request.GET['paycheck_id']
        return redirect('/paychecks/'+paycheck_id)

    # paycheck data
    if not paycheck_id:
        return HttpResponseRedirect(reverse('paycheck', args=(paychecks.first().id,)))
    else:
        paycheck = get_object_or_404(Paycheck, pk=paycheck_id, user=user)
    pay_type = PayType.objects.filter(pk=paycheck.paychecks_per_year).first()

    # calculate take home pay (paycheck gross - all deductions)
    deductions_list = Deduction.objects.filter(paycheck=paycheck, active=True, user=user)
    paycheck_gross = round(paycheck.annual_salary/paycheck.paychecks_per_year, 2)
    deduction_total = deductions_list.aggregate(Sum('amount'))['amount__sum'] or 0
    deduction_form = DeductionForm(initial={'paycheck': paycheck, 'user': request.user})

    # paystub data
    paystubs_list = Paystub.objects.order_by('-end_date').filter(paycheck=paycheck, user=user)
    for paystub in paystubs_list:
        transactions = Transaction.objects.filter(
            transaction_date__gte=paystub.start_date,
            transaction_date__lt=paystub.end_date,
            user=user,
            budget_account=BudgetAccount.objects.get(
                Q(account_type__account_type='Flex'),
                user=user,
            )
        ).exclude(notes='paystub')
        paystub.spent_in_period = transactions.aggregate(spent=Sum('amount_spent'))['spent'] or 0
    paginator = Paginator(paystubs_list, 15)
    page = request.GET.get('page')
    paged_paystubs = paginator.get_page(page)

    context = {
        'paychecks': paychecks,
        'paycheck': paycheck,
        'paycheck_gross': paycheck_gross,
        'deduction_total': deduction_total,
        'take_home_pay': paycheck_gross - deduction_total,
        'paystubs': paged_paystubs,
        'pay_type': pay_type,
        'deductions': deductions_list,
        'deduction_form': deduction_form,
    }
    return render(request, 'paychecks/paychecks.html', context)


def add_paystub(request, paycheck_id):
    user = request.user
    today = datetime.datetime.now()
    paycheck = get_object_or_404(Paycheck, pk=paycheck_id, user=user)

    budget_accounts = BudgetAccount.objects.filter(user=user, active=True).\
        exclude(Q(account_type__account_type='Flex')).order_by('name')
    TransactionFormSet = modelformset_factory(Transaction, form=TransactionPaystubForm, extra=len(budget_accounts))
    DepositFormSet = modelformset_factory(Transaction, form=TransactionPaystubForm, extra=5)

    if request.method == 'POST':
        end_date = request.POST['end_date']
        paystub_form = PaystubForm(request.POST)
        transaction_formset = TransactionFormSet(request.POST, prefix='budget')
        deposit_formset = DepositFormSet(request.POST, prefix='deposit')
        if paystub_form.is_valid() and transaction_formset.is_valid() and deposit_formset.is_valid():
            paystub = paystub_form.save(commit=False)
            paystub.user = user
            paystub.save()

            # adding necessary data for each budget contribution
            for contribution in transaction_formset.save(commit=False):
                contribution.description = 'Paycheck Contribution'
                contribution.notes = 'paystub'
                contribution.user = user
                contribution.transaction_date = end_date
                contribution.paystub = paystub
                contribution.save()

            # Creating the flex budget contribution
            flex_contribution = Transaction(
                description='Paycheck Contribution',
                notes='paystub',
                user=user,
                transaction_date=end_date,
                paystub=paystub,
                budget_account=BudgetAccount.objects.get(
                    Q(account_type__account_type='Flex'),
                    user=user,
                ),
                amount_spent=request.POST['flex_amount_spent']
            )
            flex_contribution.save()

            # adding necessary data for each money deposit
            for deposit in deposit_formset.save(commit=False):
                deposit.description = 'Payed'
                deposit.notes = 'paystub'
                deposit.user = user
                deposit.transaction_date = end_date
                deposit.paystub = paystub
                deposit.save()

            return HttpResponseRedirect(reverse('paycheck', args=(paycheck_id,)))

    transaction_data = []
    for account in budget_accounts:
        # initialize a transaction data for each budget account
        account_trans = {}
        account_trans['budget_account'] = account

        account_trans_list = Transaction.objects.filter(
            user=user, budget_account=account, paystub__isnull=False,
            transaction_date__year=today.year, transaction_date__month=today.month
        )
        account_trans['month_contribution'] = account_trans_list.aggregate(Sum('amount_spent'))['amount_spent__sum'] or 0
        account_trans['monthly_contribution'] = round(account.contribution_amount/account.month_intervals, 2)
        # initialize paycheck contribution as monthly_contribution * 12 / number of paychecks per year
        account_trans['amount_spent'] = round(account_trans['monthly_contribution']*12/paycheck.paychecks_per_year, 2)
        transaction_data.append(account_trans)
    transaction_formset = TransactionFormSet(initial=transaction_data, prefix='budget',
                                             queryset=Transaction.objects.none())

    deposit_formset = DepositFormSet(
        prefix='deposit',
        queryset=Transaction.objects.none(),
        form_kwargs={'user': user},
    )

    # initialize paycheck gross
    deductions_list = Deduction.objects.filter(paycheck=paycheck, active=True, user=user)
    paycheck_gross = round(paycheck.annual_salary/paycheck.paychecks_per_year, 2)
    deduction_total = deductions_list.aggregate(total=Coalesce(Sum('amount'), 0)).get('total')

    paystub_form = PaystubForm(initial={
        'paycheck': paycheck_id,
        'user': request.user,
        'gross_pay': paycheck_gross - deduction_total
    })

    context = {
        'paystub_form': paystub_form,
        'transaction_formset': transaction_formset,
        'deposit_formset': deposit_formset,
        'paycheck': paycheck,
    }

    return render(request, 'paychecks/paystub_create.html', context)


class PaystubDeleteView(UserPassesTestMixin, DeleteView):
    model = Paystub

    def test_func(self):
        path = self.request.path
        paystub_id = re.search('paystub/(.*)/delete', path).group(1)
        return Paystub.objects.filter(pk=paystub_id, user=self.request.user)

    def get_success_url(self):
        return reverse('paycheck', args=(self.object.paycheck.id,))


def create_deduction(request):
    if request.method == 'POST':
        paycheck_id = request.POST['paycheck']
        # double check to make sure user has access to object
        get_object_or_404(Paycheck, pk=paycheck_id, user=request.user)
        deduction = DeductionForm(request.POST)
        if deduction.is_valid():
            deduction.save()
            messages.success(request, 'New deduction has been added')
        else:
            messages.error(request, "Error creating dedeuction")
        return redirect('/paychecks/'+paycheck_id)


class DeductionUpdateView(UserPassesTestMixin, UpdateView):
    model = Deduction
    form_class = DeductionForm
    template_name = 'paychecks/deduction_update.html'

    def test_func(self):
        path = self.request.path
        deduction_id = re.search('deduction/(.*)/edit', path).group(1)
        return Deduction.objects.filter(pk=deduction_id, user=self.request.user)

    def get_success_url(self):
        get_object_or_404(Paycheck, pk=self.object.paycheck.id, user=self.request.user)
        return reverse('paycheck', args=(self.object.paycheck.id,))


class DeductionDeleteView(UserPassesTestMixin, DeleteView):
    model = Deduction

    def test_func(self):
        path = self.request.path
        deduction_id = re.search('deduction/(.*)/delete', path).group(1)
        return Deduction.objects.filter(pk=deduction_id, user=self.request.user)

    def get_success_url(self):
        return reverse('paycheck', args=(self.object.paycheck.id,))


class PaycheckCreateView(CreateView):
    model = Paycheck
    form_class = PaycheckForm
    template_name = 'paychecks/paycheck_form.html'

    def get_initial(self, *args, **kwargs):
        initial = super(PaycheckCreateView, self).get_initial(**kwargs)
        initial['user'] = self.request.user
        return initial

    def get_success_url(self):
        get_object_or_404(Paycheck, pk=self.object.id, user=self.request.user)
        return reverse('paycheck', args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Salary Paycheck'
        return context


class PaycheckUpdateView(UserPassesTestMixin, UpdateView):
    model = Paycheck
    form_class = PaycheckForm
    template_name = 'paychecks/paycheck_form.html'

    def test_func(self):
        path = self.request.path
        paycheck_id = re.search('paychecks/(.*)/edit', path).group(1)
        return Paycheck.objects.filter(pk=paycheck_id, user=self.request.user)

    def get_success_url(self):
        get_object_or_404(Paycheck, pk=self.object.id, user=self.request.user)
        return reverse('paycheck', args=(self.object.id,))
