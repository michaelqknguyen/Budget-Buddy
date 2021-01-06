import pytest
from django.test import TestCase
from budgetbuddy.stocks.tests.factories import BrokerageAccountFactory, StockSharesFactory, StockFactory, StockTransactionFactory
from budgetbuddy.stocks.models import StockShares
from budgetbuddy.accounts.tests.factories import BudgetAccountFactory
from budgetbuddy.users.tests.factories import UserFactory
pytestmark = pytest.mark.django_db


class StockFactoryTest(TestCase):
    def test_string_representation(self):
        proto_stock = StockFactory()
        self.assertEqual(str(proto_stock), proto_stock.ticker)


class StockShareFactoryTest(TestCase):
    def setUp(self):
        self.proto_stock = StockFactory()
        self.proto_broker = BrokerageAccountFactory()
        self.proto_budget = BudgetAccountFactory()
        self.user = UserFactory()

    # def test_num_owned(self):
    #     buy_num = 5

    #     stock_shares = StockSharesFactory(
    #         stock=self.proto_stock, brokerage_account=self.proto_broker,
    #         budget_account=self.proto_budget, num_shares=0)
    #     StockTransactionFactory(shares=stock_shares, transaction_type='B', num_shares=buy_num)

    #     self.assertEqual(stock_shares.num_shares, buy_num)

    def test_share_values(self):
        buy_num = 5.24
        market_price = 4.42

        stock = StockFactory(market_price=market_price)
        stock_shares = StockSharesFactory(
            stock=stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget, num_shares=buy_num)

        assert stock_shares.shares_value == buy_num * market_price

    # def test_some_sold(self):
    #     buy_num = 5
    #     sell_num = 2

    #     stock_shares = StockSharesFactory(
    #         stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
    #     StockTransactionFactory(shares=stock_shares, transaction_type='B', num_shares=buy_num)
    #     StockTransactionFactory(shares=stock_shares, transaction_type='S', num_shares=sell_num)

    #     self.assertEqual(stock_shares.num_shares_owned, buy_num-sell_num)
    #     self.assertEqual(stock_shares.num_shares_sold, sell_num)
    #     self.assertFalse(stock_shares.more_shares_sold)

    # def test_more_sold_than_bought(self):
    #     buy_num = 2
    #     sell_num = 5

    #     stock_shares = StockSharesFactory(
    #         stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
    #     StockTransactionFactory(shares=stock_shares, transaction_type='B', num_shares=buy_num)
    #     StockTransactionFactory(shares=stock_shares, transaction_type='S', num_shares=sell_num)

    #     self.assertEqual(stock_shares.num_shares_owned, buy_num-sell_num)
    #     self.assertEqual(stock_shares.num_shares_sold, sell_num)
    #     self.assertTrue(stock_shares.more_shares_sold)

    def test_manager_find_all_shares(self):
        proto_budget2 = BudgetAccountFactory()
        stock_shares = StockSharesFactory(
            user=self.user, stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
        stock_shares2 = StockSharesFactory(
            user=self.user, stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=proto_budget2)

        all_shares = StockShares.objects.find_all_shares(self.user, stock=self.proto_stock)

        self.assertQuerysetEqual(all_shares, [repr(stock_shares), repr(stock_shares2)], ordered=False)

    def test_manager_find_all_shares_one_budget(self):
        proto_budget2 = BudgetAccountFactory()
        StockSharesFactory(
            user=self.user, stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
        stock_shares2 = StockSharesFactory(
            user=self.user, stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=proto_budget2)

        all_shares = StockShares.objects.find_all_shares(user=self.user, stock=self.proto_stock, budget_account=proto_budget2)

        self.assertQuerysetEqual(all_shares, [repr(stock_shares2)], ordered=False)

    def test_investment_sum(self):
        buy_num = 5.24
        market_price = 4.42
        value = buy_num * market_price
        buy_num2 = 45.21
        market_price2 = 3.45
        value2 = buy_num2 * market_price2

        stock = StockFactory(market_price=market_price)
        stock2 = StockFactory(market_price=market_price2)
        StockSharesFactory(
            stock=stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget, num_shares=buy_num)
        StockSharesFactory(stock=stock2, brokerage_account=self.proto_broker, num_shares=buy_num2)
        investment_sum_stock1 = StockShares.objects.investment_sum(stock=stock)
        investment_sum_broker1 = StockShares.objects.investment_sum(brokerage_account=self.proto_broker)
        investment_sum_broker1_budget1 = StockShares.objects.investment_sum(brokerage_account=self.proto_broker, budget_account=self.proto_budget)

        assert float(investment_sum_stock1) == round(value, 2)
        assert float(investment_sum_broker1) == round(value + value2, 2)
        assert float(investment_sum_broker1_budget1) == round(value, 2)
