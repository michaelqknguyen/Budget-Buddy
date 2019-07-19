from django import forms
from .models import BudgetAccount, Transaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class BudgetAccountForm(forms.ModelForm):
    class Meta:
        model = BudgetAccount
        fields = ('name', 'account_type', 'contribution_amount', 'month_intervals', 'user', 'active')
        widgets = {'user': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Budget Account'))


class TransactionForm(forms.ModelForm):
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
