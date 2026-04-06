## 1. Quick fixes (no new code paths)

- [x] 1.1 Fix duplicate `calculate_investment_balance()` call in `account_view` -- replace line 201 with the `investment_balance` variable from line 187
- [x] 1.2 Add `db_index=True` to `Transaction.transaction_date` in `accounts/models.py`
- [x] 1.3 Generate and apply the migration for the new index

## 2. Decouple price fetching from balance calculation

- [x] 2.1 Remove the `Stock.objects.update_market_prices()` call from `calculate_investment_balance()` in `stocks/utils.py`, making it a pure read function
- [x] 2.2 Verify existing tests still pass after removing the side effect

## 3. AJAX stock price update endpoint

- [x] 3.1 Create a new view in `stocks/views.py` (or `accounts/views.py`) that accepts POST, calls `update_market_prices()` for the user's stocks, and returns JSON with updated investment balances
- [x] 3.2 Add the URL pattern for the new endpoint (e.g., `/budget/api/update-stock-prices/`)
- [x] 3.3 Ensure the endpoint is `@login_required` and scoped to the requesting user's stock shares

## 4. Frontend integration

- [x] 4.1 Add JavaScript to the account detail template (`account.html`) that fires a `fetch()` POST to the update endpoint after page load
- [x] 4.2 On successful response, update the displayed investment balance and stock gains values in the DOM
- [x] 4.3 Handle AJAX failure silently -- keep last-known values displayed

## 5. Verification

- [x] 5.1 Run the full test suite and fix any failures
- [x] 5.2 Run linters (black, isort, flake8, mypy) and fix any issues
- [x] 5.3 Manual test: load account detail page, confirm it renders instantly and prices update asynchronously
