from django import forms
from budgetbuddy.stocks.models import StockShares, StockTransaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class StockSharesForm(forms.ModelForm):
    class Meta:
        model = StockShares
        fields = ('user', 'stock', 'brokerage_account', 'budget_account')
        widgets = {'user': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Stock Shares'))


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ('user', 'transaction_date', 'transaction_type', 'shares', 'num_shares', 'price')
        widgets = {'user': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Stock Transaction'))
