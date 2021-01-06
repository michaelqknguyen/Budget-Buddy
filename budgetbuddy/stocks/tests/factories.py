from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from budgetbuddy.stocks.models import Stock, StockShares, StockTransaction
from budgetbuddy.users.tests.factories import UserFactory
from budgetbuddy.accounts.tests.factories import BudgetAccountFactory, BrokerageAccountFactory


class StockFactory(DjangoModelFactory):
    ticker = Faker("bothify", text="????")
    asset_class = Faker("bothify", text="????????")
    updated_at = Faker('date_between', start_date='-1y', end_date='today')
    market_price = Faker(
        'pydecimal',
        min_value=1,
        max_value=1000,
        right_digits=2
    )

    class Meta:
        model = Stock


class StockSharesFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    stock = SubFactory(StockFactory)
    brokerage_account = SubFactory(BrokerageAccountFactory)
    budget_account = SubFactory(BudgetAccountFactory)
    num_shares = Faker(
        'pydecimal',
        min_value=1,
        max_value=1000,
        right_digits=4
    )

    class Meta:
        model = StockShares


class StockTransactionFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    shares = SubFactory(StockSharesFactory)
    num_shares = Faker("random_int", min=1, max=100)
    transaction_date = Faker('date_between', start_date='-1y', end_date='today')
    transaction_type = Faker('random_element', elements=['B', 'S'])
    price = Faker(
        'pydecimal',
        min_value=1,
        max_value=1000,
        right_digits=2
    )

    class Meta:
        model = StockTransaction
