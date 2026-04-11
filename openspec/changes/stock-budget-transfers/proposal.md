## Why

Budget accounts can hold both cash (via BudgetAllocations) and stock (via StockShares). When a user needs to spend from a budget account that is stock-heavy and cash-poor, they currently have to sell stock to free up cash. A stock transfer between budget accounts allows users to send stock to another envelope and receive cash back (via a separate cash transfer), avoiding unnecessary sells. This is a re-categorization of which budget envelope "owns" the shares -- no actual money or brokerage positions change.

Additionally, the existing stock buy/sell flow (`create_stock_transaction`) lacks basic safety guardrails: no atomic transaction wrapping (partial failures leave inconsistent state), no validation against selling more shares than owned, and no sanity checking when the entered price diverges significantly from the current market price (easy to accidentally swap the shares and price fields).

## What Changes

- **Stock transfers via `StockTransaction`**: Add a "Transfer" type ("T") to `StockTransaction` along with a nullable `to_shares` FK to `StockShares`. A single `StockTransaction` record captures the transfer -- `shares` is the source, `to_shares` is the destination. No new model needed.
- **New stocks page (`/stocks/`)** providing a cross-account view of all stock holdings, a stock transfer form, and transfer history. The transfer form shows cash and stock balances for selected budget accounts to support informed decision-making.
- **Atomic transfer operation** wrapped in `transaction.atomic()` with `select_for_update()` to safely decrement/increment `StockShares.num_shares` and create the `StockTransaction` transfer record, with validation guardrails (sufficient shares, non-negative balances, different accounts).
- **Buy/sell guardrails**: Wrap existing `create_stock_transaction` in `transaction.atomic()`, reject sells when insufficient shares, and warn when entered price diverges significantly from current market price.
- **Account detail page query update**: The stock transactions query on the account detail page adds a check for `to_shares` so transfers show on the destination account's history too.

## Capabilities

### New Capabilities
- `stock-transfers`: Transfer stock shares between budget accounts using a new "Transfer" type on StockTransaction, with validation, atomicity, and an audit trail.
- `stocks-page`: New dedicated page showing all stock holdings across accounts, the stock transfer form (with cash/stock balance context), and transfer history.
- `stock-transaction-guardrails`: Atomic wrapping, sell validation, and price sanity warnings for the existing buy/sell flow.

### Modified Capabilities

(none)

## Impact

- **Models**: New `to_shares` nullable FK and "T" transaction type on `StockTransaction`, new database migration.
- **Views**: New view(s) in `stocks` app for the stocks page and transfer submission. Modified `create_stock_transaction` for guardrails. Modified account detail view query to include `to_shares`.
- **Templates**: New template(s) for the `/stocks/` page. Minor update to account detail template to handle "T" type display.
- **URLs**: New URL route(s) under `/stocks/`.
- **Navigation**: Stocks page added to the site navigation.
- **Existing buy/sell flow**: Wrapped in `transaction.atomic()`, sell validation added, price sanity warning added.
