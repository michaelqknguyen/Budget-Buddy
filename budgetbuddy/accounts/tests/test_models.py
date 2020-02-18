import pytest
from django.test import TestCase
from budgetbuddy.accounts.tests.factories import MoneyAccountFactory, BudgetAccountFactory, TransactionFactory, MoneyAccountTypeFactory

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
        self.assertEqual(self.money_account.money_or_budget, 'm')


class BudgetAccountModelTest(TestCase):
    def setUp(self):
        self.budget_account = BudgetAccountFactory()

    def test_string_representation(self):
        self.assertEqual(str(self.budget_account), self.budget_account.name)

    def test_money_or_budget_property(self):
        self.assertEqual(self.budget_account.money_or_budget, 'b')

    def test_monthly_contribution_property(self):
        self.assertEqual(
            round(self.budget_account.monthly_contribution, 5),
            round(self.budget_account.contribution_amount/self.budget_account.month_intervals, 5)
        )

    def test_annual_contribution_property(self):
        self.assertEqual(
            round(self.budget_account.annual_contribution, 5),
            round(12*self.budget_account.contribution_amount/self.budget_account.month_intervals, 5)
        )


class TransactionModelTest(TestCase):
    def test_string_representation(self):
        pass
