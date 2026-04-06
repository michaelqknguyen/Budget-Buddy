from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from django import forms
from django.forms import inlineformset_factory

from budgetbuddy.accounts.models import (
    BudgetAccount,
    BudgetAllocation,
    MoneyAccount,
    Transaction,
)


class BudgetAccountForm(forms.ModelForm):
    class Meta:
        model = BudgetAccount
        fields = (
            "name",
            "account_type",
            "contribution_amount",
            "month_intervals",
            "user",
            "assigned_paycheck",
            "active",
        )
        widgets = {"user": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Save Budget Account"))


class MoneyAccountForm(forms.ModelForm):
    class Meta:
        model = MoneyAccount
        fields = (
            "name",
            "account_type",
            "user",
            "date_opened",
            "date_closed",
            "is_brokerage",
            "active",
        )
        widgets = {"user": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Save Money Account"))


class TransactionForm(forms.ModelForm):
    money_account = forms.ModelChoiceField(
        queryset=MoneyAccount.objects.order_by("name"),
        required=False,
    )

    class Meta:
        model = Transaction
        fields = (
            "transaction_date",
            "description",
            "amount_spent",
            "money_account",
            "user",
        )
        widgets = {
            "user": forms.HiddenInput(),
            "transaction_date": forms.DateInput(
                attrs={"class": "datepicker", "type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))


class BudgetAllocationForm(forms.ModelForm):
    budget_account = forms.ModelChoiceField(
        queryset=BudgetAccount.objects.order_by("name"),
        required=True,
    )

    class Meta:
        model = BudgetAllocation
        fields = ("budget_account", "amount", "description")
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "description": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Description (optional)"}
            ),
        }


BudgetAllocationFormSet = inlineformset_factory(
    Transaction,
    BudgetAllocation,
    form=BudgetAllocationForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class ValidatedAllocationFormSet(BudgetAllocationFormSet):
    """Formset that validates allocation amounts sum to transaction.amount_spent."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        total = sum(
            form.cleaned_data.get("amount", 0)
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        )

        if hasattr(self.instance, "amount_spent") and self.instance.amount_spent is not None:
            if total != self.instance.amount_spent:
                raise forms.ValidationError(
                    f"Allocation amounts must sum to the transaction amount "
                    f"(${self.instance.amount_spent}). Currently: ${total}."
                )
