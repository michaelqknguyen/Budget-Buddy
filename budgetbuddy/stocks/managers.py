import logging
from datetime import timedelta
from decimal import Decimal

import requests  # type: ignore[import-untyped]

from django.db import models
from django.db.models import F, Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

YAHOO_CHART_URL = "https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
YAHOO_HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_stock_prices(tickers):
    """Fetch current prices for a list of tickers via Yahoo Finance chart API.

    Makes one lightweight HTTP request per ticker. Returns a dict of
    {ticker: price} with 0 for any ticker that fails.
    """
    prices: dict[str, float] = {t: 0.0 for t in tickers}
    if not tickers:
        return prices

    for ticker in tickers:
        try:
            resp = requests.get(
                YAHOO_CHART_URL.format(ticker=ticker),
                headers=YAHOO_HEADERS,
                params={"range": "1d", "interval": "1d"},
                timeout=10,
            )
            if resp.status_code == 429:
                logger.warning("Yahoo Finance rate limited, stopping batch")
                break
            resp.raise_for_status()
            data = resp.json()
            result = data.get("chart", {}).get("result")
            if result:
                price = result[0].get("meta", {}).get("regularMarketPrice")
                if price is not None:
                    prices[ticker] = float(price)
        except requests.RequestException:
            logger.exception("Failed to fetch price for %s", ticker)
        except (KeyError, IndexError, ValueError):
            logger.debug("Unexpected response structure for %s", ticker)

    return prices


class StockManager(models.Manager):

    def update_market_prices(self, update_interval=900):
        """Update market prices for shares at a specified interval.
        If the stock model hasn't been updated in the specified interval,
        pull data from Yahoo Finance.

        Also updates any stock that has never had a price fetched (market_price=0).

        Default interval is 15 minutes.
        """
        interval_start = timezone.now() - timedelta(seconds=update_interval)
        stocks_to_update = (
            super()
            .get_queryset()
            .filter(Q(updated_at__lte=interval_start) | Q(market_price=Decimal("0")))
        )
        tickers = list(stocks_to_update.values_list("ticker", flat=True))

        if not tickers:
            return

        market_prices = get_stock_prices(tickers)

        for stock in stocks_to_update:
            price = market_prices.get(stock.ticker, 0)
            if price > 0:
                stock.market_price = price
                stock.save()


class StockSharesManager(models.Manager):

    def find_all_shares(
        self, stock, user=None, brokerage_account=None, budget_account=None
    ):
        """Find all shares in all accounts for a ticker."""
        query_args = {
            "stock": stock,
            "user": user,
            "brokerage_account": brokerage_account,
            "budget_account": budget_account,
        }
        final_query_args = {k: v for k, v in query_args.items() if v is not None}
        return super().get_queryset().filter(**final_query_args)

    def investment_sum(
        self, user=None, stock=None, brokerage_account=None, budget_account=None
    ):
        """Find sum of shares in accounts."""
        query_args = {
            "user": user,
            "stock": stock,
            "brokerage_account": brokerage_account,
            "budget_account": budget_account,
        }
        final_query_args = {k: v for k, v in query_args.items() if v is not None}
        queryset = super().get_queryset().filter(**final_query_args)
        total = queryset.aggregate(
            total=Sum(F("num_shares") * F("stock__market_price"))
        )["total"]

        if total is None:
            return 0

        return round(total, 2)
