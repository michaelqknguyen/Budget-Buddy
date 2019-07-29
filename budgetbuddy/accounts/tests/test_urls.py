import pytest
from django.urls import reverse, resolve
from budgetbuddy.accounts.tests.factories import MoneyAccountFactory, BudgetAccountFactory

pytestmark = pytest.mark.django_db


class TestBudgetAccountUrl:
    def test_budget_account(self):
        proto_budget = BudgetAccountFactory()
        assert (
            reverse("budget:budget_account", kwargs={"account_id": proto_budget.id})
            == f"/budget/b/{proto_budget.id}"
        )
        assert resolve(f"/budget/b/{proto_budget.id}").view_name == "budget:budget_account"


class TestMoneyAccountUrl:
    def test_money_account(self):
        proto_money = MoneyAccountFactory()
        assert (
            reverse("budget:money_account", kwargs={"account_id": proto_money.id})
            == f"/budget/m/{proto_money.id}"
        )
        assert resolve(f"/budget/m/{proto_money.id}").view_name == "budget:money_account"
