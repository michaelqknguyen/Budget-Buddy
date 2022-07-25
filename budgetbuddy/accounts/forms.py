from django import forms
from budgetbuddy.accounts.models import BudgetAccount, MoneyAccount, Transaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class BudgetAccountForm(forms.ModelForm):
    class Meta:
        model = BudgetAccount
        fields = ('name', 'account_type', 'contribution_amount', 'month_intervals', 'user',
                  'assigned_paycheck', 'active')
        widgets = {'user': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Budget Account'))


class MoneyAccountForm(forms.ModelForm):
    class Meta:
        model = MoneyAccount
        fields = ('name', 'account_type', 'user', 'date_opened', 'date_closed', 'is_brokerage', 'active')
        widgets = {'user': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Money Account'))


class TransactionForm(forms.ModelForm):
    money_account = forms.ModelChoiceField(queryset=MoneyAccount.objects.order_by('name'))
    budget_account = forms.ModelChoiceField(queryset=BudgetAccount.objects.order_by('name'))

    class Meta:
        model = Transaction
        fields = ('transaction_date', 'description', 'amount_spent',
                  'money_account', 'budget_account', 'user')
        widgets = {
            'user': forms.HiddenInput(),
            'transaction_date': forms.DateInput(attrs={'class': 'datepicker'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))
