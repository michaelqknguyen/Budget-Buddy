import pytest
from random import randint
from django.test import TransactionTestCase
from django.db.utils import IntegrityError
from budgetbuddy.paychecks.tests.factories import PaycheckFactory, PaystubFactory, DeductionFactory
from budgetbuddy.accounts.forms import BudgetAccountForm, MoneyAccountForm, TransactionForm
from budgetbuddy.accounts.tests.factories import MoneyAccountFactory, BudgetAccountFactory, TransactionFactory
from budgetbuddy.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestBudgetAcccountForm(TransactionTestCase):
    def test_clean_budget_account(self):
        budget_account = BudgetAccountFactory()

        form = BudgetAccountForm({
            "name": budget_account.name,
            "account_type": budget_account.account_type.id,
            "contribution_amount": budget_account.contribution_amount,
            "month_intervals": budget_account.month_intervals,
            "user": budget_account.user.id,
            "active": budget_account.active
        })
        self.assertTrue(form.is_valid())
        form.save()


class TestMoneyAcccountForm(TransactionTestCase):
    def test_clean_budget_account(self):
        money_account = MoneyAccountFactory()

        form = MoneyAccountForm({
            "name": money_account.name,
            "account_type": money_account.account_type.id,
            "user": money_account.user.id,
            "active": money_account.active,
            "date_opened": money_account.date_opened,
            "date_closed": money_account.date_closed
        })
        self.assertTrue(form.is_valid())
        form.save()


class testTransactionForm(TransactionTestCase):
    def test_clean_transaction(self):
        transaction = TransactionFactory()

        form = TransactionForm({
            "transaction_date": transaction.transaction_date,
            "description": transaction.description,
            "amount_spent": transaction.amount_spent,
            "money_account": transaction.money_account.id,
            "budget_account": transaction.budget_account.id,
            "user": transaction.user.id
        })
        self.assertTrue(form.is_valid())
        form.save()
