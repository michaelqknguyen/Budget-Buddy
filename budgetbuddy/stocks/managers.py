import requests
from datetime import datetime, timedelta

from django.conf import settings
from django.db import models


def get_stock_prices(tickers):
    ticker_string = ','.join(list(tickers))
    querystring = {"region": "US", "symbols": ticker_string}
    headers = {
        'x-rapidapi-key': settings.RAPID_API_KEY,
        'x-rapidapi-host': settings.YAHOO_FINANCE_API_HOST
    }
    response = requests.request("GET", settings.YAHOO_FINANCE_QUOTES_URI, headers=headers, params=querystring)

    body = response.json()

    prices = dict()

    for quote in body.get('quoteResponse', {}).get('result', []):
        prices[quote.get('symbol')] = quote.get('regularMarketPrice')

    return prices


class StockManager(models.Manager):

    def update_market_prices(self, update_interval=900):
        """Update market prices for all shares at a specified interval
        If the stock model hasn't been updated in the specified interval, pull data from API

        default is 15 minutes
        """
        interval_start = datetime.now() - timedelta(seconds=update_interval)
        stocks_to_update = super().get_queryset().filter(updated_at__lte=interval_start)
        tickers = list(stocks_to_update.values_list('ticker', flat=True))

        if not tickers:
            # none to update -- exit
            return

        market_prices = get_stock_prices(tickers)

        for stock in stocks_to_update:
            stock.market_price = market_prices[stock.ticker]
            stock.save()


class StockSharesManager(models.Manager):
    def find_all_shares(self, user, stock=None, brokerage_account=None, budget_account=None):
        """find all shares in all accounts for a ticker"""
        query_args = {'user': user, 'stock': stock, 'brokerage_account': brokerage_account, 'budget_account': budget_account}
        # don't include the args if the value is none
        final_query_args = {k: v for k, v in query_args.items() if v is not None}
        return super().get_queryset().filter(**final_query_args)
