from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from budgetbuddy.paychecks.tests.factories import PaystubFactory
from budgetbuddy.accounts.models import MoneyAccount, BudgetAccount, Transaction, AccountType
from budgetbuddy.users.tests.factories import UserFactory

MONEY_CHOICES = ['Wallet', 'Credit Card', 'Bank']
BUDGET_CHOICES = ['Flex', 'Expense', 'Savings']


class MoneyAccountTypeFactory(DjangoModelFactory):
    account_type = Faker('random_element', elements=MONEY_CHOICES)
    is_cash_account = True

    class Meta:
        model = AccountType


class MoneyAccountFactory(DjangoModelFactory):
    name = Faker('credit_card_provider')
    user = SubFactory(UserFactory)
    account_type = SubFactory(MoneyAccountTypeFactory)

    class Meta:
        model = MoneyAccount


class BudgetAccountTypeFactory(DjangoModelFactory):
    account_type = Faker('random_element', elements=BUDGET_CHOICES)
    is_cash_account = False

    class Meta:
        model = AccountType


class BudgetAccountFactory(DjangoModelFactory):
    name = Faker('cryptocurrency_name')
    user = SubFactory(UserFactory)
    account_type = SubFactory(BudgetAccountTypeFactory)
    contribution_amount = Faker(
        'pydecimal',
        min_value=10,
        max_value=1000,
        right_digits=2
    )
    month_intervals = Faker("random_int", min=1, max=24)

    class Meta:
        model = BudgetAccount


class TransactionFactory(DjangoModelFactory):
    description = Faker('word')
    transaction_date = Faker('date_between', start_date='-1y', end_date='today')
    amount_spent = Faker(
        'pydecimal',
        min_value=-2000,
        max_value=2000,
        right_digits=2
    )
    money_account = SubFactory(MoneyAccountFactory)
    budget_account = SubFactory(BudgetAccountFactory)
    paystub = SubFactory(PaystubFactory)
    user = SubFactory(UserFactory)

    class Meta:
        model = Transaction
