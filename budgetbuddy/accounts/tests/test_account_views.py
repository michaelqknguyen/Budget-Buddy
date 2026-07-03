import pytest
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from budgetbuddy.accounts.models import BudgetAllocation
from budgetbuddy.accounts.tests.factories import (
    BudgetAccountFactory,
    BudgetAllocationFactory,
    MoneyAccountFactory,
    TransactionFactory,
)
from budgetbuddy.accounts.tests.utils import create_flex_account
from budgetbuddy.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestBudgetAccountBalance(TestCase):
    """Test balance calculation for budget account pages."""

    def setUp(self):
        self.user = UserFactory()
        self.password = "testpass"
        self.user.set_password(self.password)
        self.user.save()
        self.client.login(username=self.user.username, password=self.password)
        self.budget_account = BudgetAccountFactory(user=self.user)

    def test_budget_account_balance_single_transaction(self):
        """Test that balance correctly sums a single transaction allocation."""
        transaction = TransactionFactory(user=self.user, amount_spent=100)
        BudgetAllocationFactory(
            transaction=transaction,
            budget_account=self.budget_account,
            amount=100,
        )

        response = self.client.get(
            reverse("budget:budget_account", args=[self.budget_account.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["balance"], Decimal("100"))

    def test_budget_account_balance_split_transaction(self):
        """Test that balance uses allocation amounts, not full transaction amount, for split transactions."""
        # Create a $100 transaction
        transaction = TransactionFactory(user=self.user, amount_spent=100)

        # Split allocation: $60 to this budget account, $40 to another
        BudgetAllocationFactory(
            transaction=transaction,
            budget_account=self.budget_account,
            amount=60,
        )
        other_budget = BudgetAccountFactory(user=self.user)
        BudgetAllocationFactory(
            transaction=transaction,
            budget_account=other_budget,
            amount=40,
        )

        # Check this account's balance - should be 60, not 100
        response = self.client.get(
            reverse("budget:budget_account", args=[self.budget_account.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["balance"], Decimal("60"))

    def test_budget_account_balance_multiple_split_transactions(self):
        """Test balance calculation with multiple split transactions."""
        # Transaction 1: $100 split as $60 to this account, $40 to other
        txn1 = TransactionFactory(user=self.user, amount_spent=100)
        BudgetAllocationFactory(
            transaction=txn1,
            budget_account=self.budget_account,
            amount=60,
        )
        other_budget = BudgetAccountFactory(user=self.user)
        BudgetAllocationFactory(
            transaction=txn1,
            budget_account=other_budget,
            amount=40,
        )

        # Transaction 2: $200 split as $80 to this account, $120 to other
        txn2 = TransactionFactory(user=self.user, amount_spent=200)
        BudgetAllocationFactory(
            transaction=txn2,
            budget_account=self.budget_account,
            amount=80,
        )
        BudgetAllocationFactory(
            transaction=txn2,
            budget_account=other_budget,
            amount=120,
        )

        # Check this account's balance: should be 60 + 80 = 140
        response = self.client.get(
            reverse("budget:budget_account", args=[self.budget_account.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["balance"], Decimal("140"))

    def test_budget_account_balance_negative_transactions(self):
        """Test balance calculation with negative (withdrawal) transactions."""
        # Positive transaction: +$100
        txn1 = TransactionFactory(user=self.user, amount_spent=100)
        BudgetAllocationFactory(
            transaction=txn1,
            budget_account=self.budget_account,
            amount=100,
        )

        # Negative transaction: -$30
        txn2 = TransactionFactory(user=self.user, amount_spent=-30)
        BudgetAllocationFactory(
            transaction=txn2,
            budget_account=self.budget_account,
            amount=-30,
        )

        # Balance should be 100 - 30 = 70
        response = self.client.get(
            reverse("budget:budget_account", args=[self.budget_account.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["balance"], Decimal("70"))

    def test_budget_account_balance_no_allocations(self):
        """Test that balance is zero when there are no allocations for the account."""
        # Create allocations but for a different account
        other_budget = BudgetAccountFactory(user=self.user)
        transaction = TransactionFactory(user=self.user, amount_spent=100)
        BudgetAllocationFactory(
            transaction=transaction,
            budget_account=other_budget,
            amount=100,
        )

        response = self.client.get(
            reverse("budget:budget_account", args=[self.budget_account.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["balance"], Decimal("0"))


class TestMoneyAccountBalance(TestCase):
    """Test balance calculation for money account pages."""

    def setUp(self):
        self.user = UserFactory()
        self.password = "testpass"
        self.user.set_password(self.password)
        self.user.save()
        self.client.login(username=self.user.username, password=self.password)
        self.money_account = MoneyAccountFactory(user=self.user)

    def test_money_account_balance_single_transaction(self):
        """Test that balance correctly sums a single transaction."""
        TransactionFactory(user=self.user, money_account=self.money_account, amount_spent=500)

        response = self.client.get(
            reverse("budget:money_account", args=[self.money_account.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["balance"], Decimal("500"))

    def test_money_account_balance_multiple_transactions(self):
        """Test that balance correctly sums multiple transactions."""
        TransactionFactory(user=self.user, money_account=self.money_account, amount_spent=500)
        TransactionFactory(user=self.user, money_account=self.money_account, amount_spent=300)
        TransactionFactory(user=self.user, money_account=self.money_account, amount_spent=-100)

        response = self.client.get(
            reverse("budget:money_account", args=[self.money_account.id])
        )

        self.assertEqual(response.status_code, 200)
        # 500 + 300 - 100 = 700
        self.assertEqual(response.context["balance"], Decimal("700"))

    def test_money_account_balance_no_transactions(self):
        """Test that balance is zero when there are no transactions."""
        response = self.client.get(
            reverse("budget:money_account", args=[self.money_account.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["balance"], Decimal("0"))


class TestAllAccountsBalance(TestCase):
    """Test balance calculation for the all accounts page."""

    def setUp(self):
        self.user = UserFactory()
        self.password = "testpass"
        self.user.set_password(self.password)
        self.user.save()
        self.client.login(username=self.user.username, password=self.password)

    def test_all_accounts_shows_money_account_balance(self):
        """Test that all accounts view only counts money account transactions."""
        # Create a money account with transactions
        money_account = MoneyAccountFactory(user=self.user)
        TransactionFactory(user=self.user, money_account=money_account, amount_spent=500)
        TransactionFactory(user=self.user, money_account=money_account, amount_spent=300)

        # Create a budget account with allocations
        budget_account = BudgetAccountFactory(user=self.user)
        txn = TransactionFactory(user=self.user, amount_spent=200)
        BudgetAllocationFactory(
            transaction=txn,
            budget_account=budget_account,
            amount=200,
        )

        response = self.client.get(reverse("budget:all_accounts"))

        self.assertEqual(response.status_code, 200)
        # Should only include money account balance: 500 + 300 = 800
        self.assertEqual(response.context["balance"], Decimal("800"))
