import pytest
from random import randint
from django.test import TransactionTestCase
from django.db.utils import IntegrityError
from budgetbuddy.paychecks.forms import PaycheckForm, DeductionForm, PaystubForm, TransactionPaystubForm
from budgetbuddy.paychecks.tests.factories import PaycheckFactory, PaystubFactory, DeductionFactory
from budgetbuddy.accounts.tests.factories import MoneyAccountFactory, BudgetAccountFactory, TransactionFactory
from budgetbuddy.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestPaycheckForm:
    def test_clean_paycheck(self):
        proto_paycheck = PaycheckFactory.build()
        proto_user = UserFactory.create()

        form = PaycheckForm({
            "company": proto_paycheck.company,
            "annual_salary": proto_paycheck.annual_salary,
            "paychecks_per_year": proto_paycheck.paychecks_per_year,
            "user": proto_user.id,
        })
        assert form.is_valid()
        form.save()


class TestDeductionForm:
    def test_clean_deduction(self):
        proto_paycheck = PaycheckFactory.create()
        proto_user = UserFactory.create()
        proto_deduction = DeductionFactory.build()

        form = DeductionForm({
            "paycheck": proto_paycheck.id,
            "description": proto_deduction.description,
            "deduction_type": proto_deduction.deduction_type,
            "amount": proto_deduction.amount,
            "user": proto_user.id,
        })
        assert form.is_valid()
        form.save()


class TestPaystubForm(TransactionTestCase):
    def test_clean_paystub(self):
        proto_paystub = PaystubFactory.build()
        proto_paycheck = PaycheckFactory.create()
        proto_user = UserFactory.create()

        form = PaystubForm({
            "paycheck": proto_paycheck.id,
            "gross_pay": proto_paystub.gross_pay,
            "start_date": proto_paystub.start_date,
            "end_date": proto_paystub.end_date,
        })
        assert form.is_valid()

        # user is still needed
        with self.assertRaises(IntegrityError):
            form.save()

        paystub = form.save(commit=False)
        paystub.user = proto_user
        paystub.save()


class TestTransactionPaystubForm(TransactionTestCase):
    def test_clean_transaction_paystub(self):
        proto_money = MoneyAccountFactory.create()
        proto_budget = BudgetAccountFactory.create()
        proto_transaction = TransactionFactory.build()

        form = TransactionPaystubForm({
            "amount_spent": proto_transaction.amount_spent,
            "budget_account": proto_budget.id,
            "money_account": proto_money.id,
            "monthly_contribution": 40.2,
            "month_contribution": 30.2
        })
        assert form.is_valid()

        # user, transaction_date, description still needed
        with self.assertRaises(IntegrityError):
            form.save()

        form.save(commit=False)

    def test_money_accounts_in_form(self):
        proto_user = UserFactory.create()
        proto_moneys = MoneyAccountFactory.create_batch(
            randint(1, 10),
            user=proto_user,
        )
        proto_budget = BudgetAccountFactory.create(user=proto_user)
        proto_transaction = TransactionFactory.build(user=proto_user)

        form = TransactionPaystubForm({
            "amount_spent": proto_transaction.amount_spent,
            "budget_account": proto_budget.id,
            # "money_account": proto_money.id,
            "monthly_contribution": 40.2,
            "month_contribution": 30.2
        }, user=proto_user)
        assert form.is_valid()

        # user, transaction_date, description still needed
        with self.assertRaises(IntegrityError):
            form.save()

        # show money_account list made
        self.assertEqual(len(proto_moneys), form.fields['money_account'].queryset.count())
        self.assertQuerysetEqual(
            form.fields['money_account'].queryset,
            [repr(m) for m in proto_moneys],
            ordered=False
        )
