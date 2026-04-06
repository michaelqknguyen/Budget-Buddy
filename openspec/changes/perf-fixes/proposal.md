## Why

The account detail view (`account_view`) makes synchronous HTTP requests to Yahoo Finance inside the request/response cycle, blocking page loads for seconds when stock prices are stale. Additionally, the same expensive function (`calculate_investment_balance`) is called twice per page load, and the heavily-filtered `transaction_date` field lacks a database index, causing full table scans on every date-range query.

## What Changes

- Move stock price fetching out of the view layer into an async mechanism (AJAX endpoint + background trigger), so pages load instantly and prices update asynchronously.
- Eliminate the duplicate `calculate_investment_balance()` call in `account_view` by reusing the already-computed variable.
- Add a database index on `Transaction.transaction_date` to speed up date-range queries used on every account detail page.

## Capabilities

### New Capabilities
- `async-stock-prices`: Asynchronous stock price updating via an AJAX endpoint, replacing the synchronous in-view Yahoo Finance HTTP calls.

### Modified Capabilities
- `yfinance-stock-prices`: Stock price updates are no longer triggered synchronously inside `calculate_investment_balance()`. The view becomes a pure read; price fetching moves to a dedicated endpoint.

## Impact

- **Code**: `budgetbuddy/stocks/utils.py` (remove `update_market_prices()` call from `calculate_investment_balance`), `budgetbuddy/accounts/views.py` (fix duplicate call, add AJAX endpoint or trigger), `budgetbuddy/stocks/managers.py` (may need a view-callable update path), `budgetbuddy/accounts/models.py` (add index), new migration for the index.
- **Templates**: Account detail template needs JS to trigger async price refresh and update displayed values.
- **URLs**: New endpoint for async stock price update.
- **Dependencies**: None new -- uses existing `requests` library and Django infrastructure.
