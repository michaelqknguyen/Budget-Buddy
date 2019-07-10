from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Sum
from django.core.paginator import Paginator
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from .models import Paycheck, PayType, Deduction, Paystub
from .forms import DeductionForm


def index(request, paycheck_id=1):
    user = request.user
    paychecks = Paycheck.objects.filter(active=True, user=user)

    # if form get, get the requested paycheck_id
    if 'paycheck_id' in request.GET:
        paycheck_id = request.GET['paycheck_id']
        return redirect('/paychecks/'+paycheck_id)

    # paycheck data
    paycheck = get_object_or_404(Paycheck, pk=paycheck_id, user=user)
    pay_type = get_object_or_404(PayType, pk=paycheck.paychecks_per_year, user=user)

    # calculate take home pay (paycheck gross - all deductions)
    deductions_list = Deduction.objects.filter(paycheck=paycheck, active=True, user=user)
    paycheck_gross = round(paycheck.annual_salary/paycheck.paychecks_per_year, 2)
    deduction_total = deductions_list.aggregate(Sum('amount'))['amount__sum'] or 0
    deduction_form = DeductionForm(initial={'paycheck': paycheck})

    # paystub data
    paystubs_list = Paystub.objects.order_by('end_date').filter(paycheck=paycheck, user=user)
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


def create_deduction(request):
    if request.method == 'POST':
        paycheck_id = request.POST['paycheck']
        deduction = DeductionForm(request.POST)
        if deduction.is_valid():
            deduction.save()
            messages.success(request, 'New deduction has been added')
        return redirect('/paychecks/'+paycheck_id)


class DeductionUpdateView(UserPassesTestMixin, UpdateView):
    model = Deduction
    form_class = DeductionForm
    template_name = 'paychecks/deduction_update.html'

    def test_func(self):
        print(self.request)
        return True

    def get_success_url(self):
        return reverse('paycheck', args=(self.object.paycheck.id,))


class DeductionDeleteView(DeleteView):
    model = Deduction

    def get_success_url(self):
        return reverse('paycheck', args=(self.object.paycheck.id,))
