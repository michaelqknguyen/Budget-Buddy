from decimal import Decimal

import pytest

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.test import TestCase

from budgetbuddy.accounts.models import BudgetAllocation
from budgetbuddy.accounts.tests.factories import (
    BudgetAccountFactory,
    BudgetAllocationFactory,
    MoneyAccountFactory,
    MoneyAccountTypeFactory,
    TransactionFactory,
)
from budgetbuddy.accounts.utils import round_up

pytestmark = pytest.mark.django_db


class AccountTypeModelTest(TestCase):
    def test_string_representation(self):
        proto_account_type = MoneyAccountTypeFactory()
        self.assertEqual(str(proto_account_type), proto_account_type.account_type)


class MoneyAccountModelTest(TestCase):
    def setUp(self):
        self.money_account = MoneyAccountFactory()

    def test_string_representation(self):
        self.assertEqual(str(self.money_account), self.money_account.name)

    def test_money_or_budget_property(self):
        self.assertEqual(self.money_account.money_or_budget, "m")


class BudgetAccountModelTest(TestCase):
    def setUp(self):
        self.budget_account = BudgetAccountFactory()

    def test_string_representation(self):
        self.assertEqual(str(self.budget_account), self.budget_account.name)

    def test_money_or_budget_property(self):
        self.assertEqual(self.budget_account.money_or_budget, "b")

    def test_monthly_contribution_property(self):
        self.assertEqual(
            round_up(self.budget_account.monthly_contribution, 5),
            round_up(
                self.budget_account.contribution_amount
                / self.budget_account.month_intervals,
                5,
            ),
        )

    def test_annual_contribution_property(self):
        self.assertEqual(
            round_up(self.budget_account.annual_contribution, 5),
            round_up(
                12
                * self.budget_account.contribution_amount
                / self.budget_account.month_intervals,
                5,
            ),
        )


class TransactionModelTest(TestCase):
    def test_string_representation(self):
        transaction = TransactionFactory(description="Groceries", amount_spent=Decimal("50.00"))
        self.assertEqual(str(transaction), "Groceries (50.00)")


class BudgetAllocationModelTest(TestCase):
    def test_string_representation(self):
        budget = BudgetAccountFactory(name="Groceries")
        allocation = BudgetAllocationFactory(
            budget_account=budget, amount=Decimal("75.00")
        )
        self.assertEqual(str(allocation), "Groceries - 75.00")

    def test_single_allocation(self):
        """A transaction with one allocation links to one budget account."""
        transaction = TransactionFactory(amount_spent=Decimal("100.00"))
        budget = BudgetAccountFactory()
        alloc = BudgetAllocationFactory(
            transaction=transaction, budget_account=budget, amount=Decimal("100.00")
        )

        self.assertEqual(transaction.allocations.count(), 1)
        self.assertEqual(transaction.allocations.first(), alloc)
        self.assertEqual(alloc.budget_account, budget)

    def test_split_allocation_create(self):
        """A transaction can be split across multiple budget accounts."""
        transaction = TransactionFactory(amount_spent=Decimal("150.00"))
        budget1 = BudgetAccountFactory()
        budget2 = BudgetAccountFactory()
        budget3 = BudgetAccountFactory()

        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget1, amount=Decimal("80.00"),
            description="groceries",
        )
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget2, amount=Decimal("40.00"),
            description="household",
        )
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget3, amount=Decimal("30.00"),
            description="clothing",
        )

        self.assertEqual(transaction.allocations.count(), 3)
        total = sum(a.amount for a in transaction.allocations.all())
        self.assertEqual(total, Decimal("150.00"))

    def test_edit_single_to_split(self):
        """Editing a single-allocation transaction to become a split."""
        transaction = TransactionFactory(amount_spent=Decimal("100.00"))
        budget1 = BudgetAccountFactory()
        budget2 = BudgetAccountFactory()

        # Start with a single allocation
        alloc = BudgetAllocationFactory(
            transaction=transaction, budget_account=budget1, amount=Decimal("100.00")
        )
        self.assertEqual(transaction.allocations.count(), 1)

        # Edit: delete the single allocation and create two
        alloc.delete()
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget1, amount=Decimal("60.00")
        )
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget2, amount=Decimal("40.00")
        )

        self.assertEqual(transaction.allocations.count(), 2)
        total = sum(a.amount for a in transaction.allocations.all())
        self.assertEqual(total, Decimal("100.00"))

    def test_edit_split_to_single(self):
        """Editing a split transaction back to a single allocation."""
        transaction = TransactionFactory(amount_spent=Decimal("100.00"))
        budget1 = BudgetAccountFactory()
        budget2 = BudgetAccountFactory()

        # Start with split allocations
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget1, amount=Decimal("60.00")
        )
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget2, amount=Decimal("40.00")
        )
        self.assertEqual(transaction.allocations.count(), 2)

        # Edit: delete all and create single
        transaction.allocations.all().delete()
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget1, amount=Decimal("100.00")
        )

        self.assertEqual(transaction.allocations.count(), 1)

    def test_delete_cascades_allocations(self):
        """Deleting a transaction cascades to delete its allocations."""
        transaction = TransactionFactory(amount_spent=Decimal("100.00"))
        budget = BudgetAccountFactory()
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget, amount=Decimal("60.00")
        )
        BudgetAllocationFactory(
            transaction=transaction, budget_account=budget, amount=Decimal("40.00")
        )

        transaction_id = transaction.id
        self.assertEqual(BudgetAllocation.objects.filter(transaction_id=transaction_id).count(), 2)

        transaction.delete()

        self.assertEqual(BudgetAllocation.objects.filter(transaction_id=transaction_id).count(), 0)

    def test_budget_balance_with_splits(self):
        """Budget account balance correctly sums allocations from split transactions."""
        budget1 = BudgetAccountFactory()
        budget2 = BudgetAccountFactory()

        # Transaction 1: fully allocated to budget1
        txn1 = TransactionFactory(amount_spent=Decimal("100.00"))
        BudgetAllocationFactory(
            transaction=txn1, budget_account=budget1, amount=Decimal("100.00")
        )

        # Transaction 2: split across budget1 and budget2
        txn2 = TransactionFactory(amount_spent=Decimal("150.00"))
        BudgetAllocationFactory(
            transaction=txn2, budget_account=budget1, amount=Decimal("80.00")
        )
        BudgetAllocationFactory(
            transaction=txn2, budget_account=budget2, amount=Decimal("70.00")
        )

        # Transaction 3: fully allocated to budget2
        txn3 = TransactionFactory(amount_spent=Decimal("50.00"))
        BudgetAllocationFactory(
            transaction=txn3, budget_account=budget2, amount=Decimal("50.00")
        )

        # Verify balance per budget account using the same annotation as views
        from budgetbuddy.accounts.models import BudgetAccount
        accounts = BudgetAccount.objects.filter(
            id__in=[budget1.id, budget2.id]
        ).annotate(
            total=Coalesce(Sum("allocations__amount"), Decimal(0))
        )

        b1 = accounts.get(id=budget1.id)
        b2 = accounts.get(id=budget2.id)

        # budget1: 100.00 + 80.00 = 180.00
        self.assertEqual(b1.total, Decimal("180.00"))
        # budget2: 70.00 + 50.00 = 120.00
        self.assertEqual(b2.total, Decimal("120.00"))
