## 1. Model Changes & Migration

- [x] 1.1 Add "T" (Transfer) to `StockTransaction.TRANSACTION_CHOICES` in `budgetbuddy/stocks/models.py`
- [x] 1.2 Add nullable `to_shares` FK to `StockShares` on `StockTransaction` with `related_name="transfers_in"`
- [ ] 1.3 Generate and review the database migration

## 2. Buy/Sell Guardrails

- [ ] 2.1 Wrap the existing `create_stock_transaction` view in `transaction.atomic()`
- [ ] 2.2 Add sell validation: reject if `num_shares > stock_shares.num_shares`, return error message
- [ ] 2.3 Add price sanity warning: if entered price is < 50% or > 200% of `stock.market_price`, return a warning requiring confirmation (skip if market_price is null)

## 3. Transfer Logic

- [ ] 3.1 Create transfer view function in `budgetbuddy/stocks/views.py` that accepts POST with source budget account, stock, destination budget account, and number of shares
- [ ] 3.2 Implement validation: positive share count, different source/destination accounts, source has sufficient shares
- [ ] 3.3 Implement atomic transfer operation: `transaction.atomic()` with `select_for_update()` on source StockShares, `get_or_create` destination StockShares, decrement/increment `num_shares`, create `StockTransaction` with type="T", shares=source, to_shares=destination, price=market price
- [ ] 3.4 Add URL route for the transfer POST endpoint under `/stocks/`

## 4. Account Detail Page Updates

- [ ] 4.1 Update stock transactions query in `account_view` to include `Q(to_shares__in=all_stock_shares)` so transfers appear on destination accounts
- [ ] 4.2 Update account detail template to display "T" type transfers differently from buys/sells (e.g., "Transfer from X" / "Transfer to X")

## 5. Stocks Page

- [ ] 5.1 Create stocks overview view in `budgetbuddy/stocks/views.py` that fetches all StockShares (num_shares > 0) for the user, all BudgetAccounts with their cash balances and investment sums, and transfer history (StockTransactions with type="T")
- [ ] 5.2 Add URL route for the stocks page at `/stocks/`
- [ ] 5.3 Create stocks page template with holdings table (ticker, shares, market value, budget account, brokerage account)
- [ ] 5.4 Add stock transfer form to the template with source/destination budget account selectors showing cash and stock balances, stock selector, and share count input
- [ ] 5.5 Add transfer history section to the template showing date, ticker, shares, source, destination, and value at transfer
- [ ] 5.6 Handle form validation errors: re-display form with error messages and preserved input values
- [ ] 5.7 Require authentication on the stocks page view (login_required)

## 6. Navigation & Integration

- [ ] 6.1 Add stocks page link to the site navigation in the base/sidebar template
- [ ] 6.2 Wire up the stocks page URL configuration in `config/urls.py` or the stocks app URL conf

## 7. Dynamic Form Behavior

- [ ] 7.1 Add JavaScript to dynamically update displayed cash/stock balances when the user changes the selected budget accounts in the transfer form
- [ ] 7.2 Add JavaScript to update available shares display when the user changes the selected stock or source budget account
