from decimal import Decimal

import pytest

from django.test import TransactionTestCase

from budgetbuddy.accounts.forms import (
    BudgetAccountForm,
    MoneyAccountForm,
    TransactionForm,
    ValidatedAllocationFormSet,
)
from budgetbuddy.accounts.models import BudgetAllocation, Transaction
from budgetbuddy.accounts.tests.factories import (
    BudgetAccountFactory,
    MoneyAccountFactory,
    TransactionFactory,
)

pytestmark = pytest.mark.django_db


class TestBudgetAcccountForm(TransactionTestCase):
    def test_clean_budget_account(self):
        budget_account = BudgetAccountFactory()

        form = BudgetAccountForm(
            {
                "name": budget_account.name,
                "account_type": budget_account.account_type.id,
                "contribution_amount": budget_account.contribution_amount,
                "month_intervals": budget_account.month_intervals,
                "user": budget_account.user.id,
                "active": budget_account.active,
            }
        )
        self.assertTrue(form.is_valid())
        form.save()


class TestMoneyAcccountForm(TransactionTestCase):
    def test_clean_budget_account(self):
        money_account = MoneyAccountFactory()

        form = MoneyAccountForm(
            {
                "name": money_account.name,
                "account_type": money_account.account_type.id,
                "user": money_account.user.id,
                "active": money_account.active,
                "date_opened": money_account.date_opened,
                "date_closed": money_account.date_closed,
            }
        )
        self.assertTrue(form.is_valid())
        form.save()


class TestTransactionForm(TransactionTestCase):
    def test_clean_transaction(self):
        transaction = TransactionFactory()

        form = TransactionForm(
            {
                "transaction_date": transaction.transaction_date,
                "description": transaction.description,
                "amount_spent": transaction.amount_spent,
                "money_account": transaction.money_account.id,
                "user": transaction.user.id,
            }
        )
        self.assertTrue(form.is_valid())
        form.save()


class TestBudgetAllocationFormSet(TransactionTestCase):
    """Tests for ValidatedAllocationFormSet (single and split allocations)."""

    def _get_formset_data(self, budget_accounts_and_amounts, prefix="allocations"):
        """Build management form + row data for the allocation formset."""
        data = {
            f"{prefix}-TOTAL_FORMS": str(len(budget_accounts_and_amounts)),
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "1",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
        for i, (ba, amount, desc) in enumerate(budget_accounts_and_amounts):
            data[f"{prefix}-{i}-budget_account"] = str(ba.id)
            data[f"{prefix}-{i}-amount"] = str(amount)
            data[f"{prefix}-{i}-description"] = desc
        return data

    def test_single_allocation(self):
        """A single allocation matching the transaction amount is valid."""
        transaction = TransactionFactory(amount_spent=Decimal("100.00"))
        budget = BudgetAccountFactory()

        data = self._get_formset_data(
            [(budget, Decimal("100.00"), "")], prefix="allocations"
        )
        formset = ValidatedAllocationFormSet(
            data, instance=transaction, prefix="allocations"
        )
        self.assertTrue(formset.is_valid())
        formset.save()

        self.assertEqual(
            BudgetAllocation.objects.filter(transaction=transaction).count(), 1
        )
        alloc = BudgetAllocation.objects.get(transaction=transaction)
        self.assertEqual(alloc.budget_account, budget)
        self.assertEqual(alloc.amount, Decimal("100.00"))

    def test_split_allocation(self):
        """Multiple allocations summing to transaction amount are valid."""
        transaction = TransactionFactory(amount_spent=Decimal("150.00"))
        budget1 = BudgetAccountFactory()
        budget2 = BudgetAccountFactory()
        budget3 = BudgetAccountFactory()

        data = self._get_formset_data(
            [
                (budget1, Decimal("80.00"), "groceries"),
                (budget2, Decimal("40.00"), "household"),
                (budget3, Decimal("30.00"), "clothing"),
            ],
            prefix="allocations",
        )
        formset = ValidatedAllocationFormSet(
            data, instance=transaction, prefix="allocations"
        )
        self.assertTrue(formset.is_valid())
        formset.save()

        allocations = BudgetAllocation.objects.filter(
            transaction=transaction
        ).order_by("amount")
        self.assertEqual(allocations.count(), 3)
        self.assertEqual(
            sum(a.amount for a in allocations), Decimal("150.00")
        )

    def test_empty_formset_invalid(self):
        """A formset with zero allocation rows is invalid (min_num=1)."""
        transaction = TransactionFactory(amount_spent=Decimal("50.00"))

        data = {
            "allocations-TOTAL_FORMS": "0",
            "allocations-INITIAL_FORMS": "0",
            "allocations-MIN_NUM_FORMS": "1",
            "allocations-MAX_NUM_FORMS": "1000",
        }
        formset = ValidatedAllocationFormSet(
            data, instance=transaction, prefix="allocations"
        )
        self.assertFalse(formset.is_valid())

    def test_sum_mismatch_invalid(self):
        """Allocations that don't sum to transaction amount are rejected."""
        transaction = TransactionFactory(amount_spent=Decimal("100.00"))
        budget1 = BudgetAccountFactory()
        budget2 = BudgetAccountFactory()

        data = self._get_formset_data(
            [
                (budget1, Decimal("60.00"), ""),
                (budget2, Decimal("30.00"), ""),  # sum = 90, should be 100
            ],
            prefix="allocations",
        )
        formset = ValidatedAllocationFormSet(
            data, instance=transaction, prefix="allocations"
        )
        self.assertFalse(formset.is_valid())
        self.assertTrue(
            any("must sum to" in str(e) for e in formset.non_form_errors())
        )
