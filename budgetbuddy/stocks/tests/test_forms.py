import pytest
from django.test import TransactionTestCase
from budgetbuddy.stocks.tests.factories import StockTransactionFactory
from budgetbuddy.stocks.forms import StockTransactionForm

pytestmark = pytest.mark.django_db


class TestStockTransactionForm(TransactionTestCase):
    def test_clean_stock_transaction(self):
        stock_transaction = StockTransactionFactory()

        form = StockTransactionForm({
            "user": stock_transaction.user.id,
            "transaction_date": stock_transaction.transaction_date,
            "transaction_type": stock_transaction.transaction_type,
            "shares": stock_transaction.shares.id,
            "num_shares": stock_transaction.num_shares,
            "price": stock_transaction.price,
        })
        self.assertTrue(form.is_valid())
        form.save()
