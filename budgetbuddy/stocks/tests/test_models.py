import pytest
from django.test import TestCase
from budgetbuddy.stocks.tests.factories import BrokerageAccountFactory, StockSharesFactory, StockFactory, StockTransactionFactory
from budgetbuddy.stocks.models import StockShares
from budgetbuddy.accounts.tests.factories import BudgetAccountFactory
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

    def test_num_owned(self):
        buy_num = 5

        stock_shares = StockSharesFactory(
            stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
        StockTransactionFactory(shares=stock_shares, transaction_type='B', num_shares=buy_num)

        self.assertEqual(stock_shares.num_shares_owned, buy_num)

    def test_some_sold(self):
        buy_num = 5
        sell_num = 2

        stock_shares = StockSharesFactory(
            stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
        StockTransactionFactory(shares=stock_shares, transaction_type='B', num_shares=buy_num)
        StockTransactionFactory(shares=stock_shares, transaction_type='S', num_shares=sell_num)

        self.assertEqual(stock_shares.num_shares_owned, buy_num-sell_num)
        self.assertEqual(stock_shares.num_shares_sold, sell_num)
        self.assertFalse(stock_shares.more_shares_sold)

    def test_more_sold_than_bought(self):
        buy_num = 2
        sell_num = 5

        stock_shares = StockSharesFactory(
            stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
        StockTransactionFactory(shares=stock_shares, transaction_type='B', num_shares=buy_num)
        StockTransactionFactory(shares=stock_shares, transaction_type='S', num_shares=sell_num)

        self.assertEqual(stock_shares.num_shares_owned, buy_num-sell_num)
        self.assertEqual(stock_shares.num_shares_sold, sell_num)
        self.assertTrue(stock_shares.more_shares_sold)

    def test_manager_find_all_shares(self):
        proto_budget2 = BudgetAccountFactory()
        stock_shares = StockSharesFactory(
            stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
        stock_shares2 = StockSharesFactory(
            stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=proto_budget2)

        all_shares = StockShares.objects.find_all_shares(self.proto_stock)

        self.assertQuerysetEqual(all_shares, [repr(stock_shares), repr(stock_shares2)], ordered=False)

    def test_manager_find_all_shares_one_budget(self):
        proto_budget2 = BudgetAccountFactory()
        StockSharesFactory(
            stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=self.proto_budget)
        stock_shares2 = StockSharesFactory(
            stock=self.proto_stock, brokerage_account=self.proto_broker, budget_account=proto_budget2)

        all_shares = StockShares.objects.find_all_shares(self.proto_stock, budget_account=proto_budget2)

        self.assertQuerysetEqual(all_shares, [repr(stock_shares2)], ordered=False)
