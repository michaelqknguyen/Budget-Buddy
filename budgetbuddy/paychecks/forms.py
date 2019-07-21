from django import forms
from .models import Deduction, Paystub, Paycheck
from accounts.models import MoneyAccount
from accounts.models import Transaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class PaycheckForm(forms.ModelForm):
    class Meta:
        model = Paycheck
        fields = ('company', 'annual_salary', 'paychecks_per_year', 'active',
                  'creation_date', 'user')
        labels = {
            'creation_date': 'Start Date',
        }
        widgets = {'user': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Salary Information'))


class DeductionForm(forms.ModelForm):
    class Meta:
        model = Deduction
        fields = ('paycheck', 'description', 'deduction_type', 'amount', 'user')
        widgets = {'paycheck': forms.HiddenInput(), 'user': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Deduction'))


class PaystubForm(forms.ModelForm):
    class Meta:
        model = Paystub
        fields = ('paycheck', 'gross_pay', 'start_date', 'end_date')
        exclude = ('user',)
        widgets = {
            'paycheck': forms.HiddenInput(),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control mb-2',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control mb-2',
                'type': 'date',
                'id': 'endDate',
            }),
            'gross_pay': forms.NumberInput(attrs={
                'class': 'form-control',
                'onchange': 'setTwoNumberDecimal',
                'id': 'moneyInput3',
            }),
        }
        labels = {
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'gross_pay': 'Paystub Gross',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Paystub'))


class TransactionPaystubForm(forms.ModelForm):
    # adding data for context
    # expected contribution monthly
    monthly_contribution = forms.DecimalField(decimal_places=2, max_digits=8, required=False)
    # actual contribution this month
    month_contribution = forms.DecimalField(decimal_places=2, max_digits=8, required=False)

    class Meta:
        model = Transaction
        fields = ('amount_spent', 'budget_account', 'money_account',
                  'monthly_contribution', 'month_contribution')
        exclude = ('user', 'transaction_date', 'description', 'notes', 'paystub')
        widgets = {
            'budget_account': forms.HiddenInput(),
            'money_account': forms.Select(attrs={
                'class': 'form-control mb-2',
            }),
            'amount_spent': forms.NumberInput(attrs={
                'class': 'form-control contribution'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['money_account'].queryset = MoneyAccount.objects.filter(user=self.user, active=True)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))
