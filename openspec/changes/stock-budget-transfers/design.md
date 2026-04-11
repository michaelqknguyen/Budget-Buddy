## Context

BudgetBuddy uses an envelope budgeting model. `MoneyAccount` tracks where money physically is (bank, brokerage), while `BudgetAccount` tracks how money is allocated (Car Fund, Retirement, etc.). Stock holdings are tracked via `StockShares`, keyed by the combination of `(user, stock, brokerage_account, budget_account)`. Each buy/sell is recorded as a `StockTransaction` lot (with per-share price) and a corresponding monetary `Transaction` with `BudgetAllocation`.

Currently, transfers exist only for cash -- budget-to-budget or money-to-money -- creating paired monetary `Transaction` records. There is no mechanism to re-categorize stock holdings between budget accounts. Users who need cash from a stock-heavy envelope must sell, even when another envelope has liquid cash to spare.

The existing `StockShares.num_shares` denormalized field is the source of truth for all balance/value displays. Computed properties like `num_shares_owned` (aggregated from `StockTransaction` records) exist but are unused in production views. `StockTransaction` is used only for display (history table on account detail page) and CRUD -- no calculations are derived from it. Per-account gains calculations use string-matching on monetary `Transaction.description` and are already imprecise.

The existing `create_stock_transaction` view has no `transaction.atomic()` wrapper, no sell validation, and no price sanity checks.

## Goals / Non-Goals

**Goals:**
- Allow users to transfer any number of stock shares from one budget account to another within the same brokerage account
- Record transfers with an audit trail visible in stock transaction history
- Ensure data integrity via atomic operations and validation for both transfers and existing buy/sell
- Provide a new stocks page with cross-account holdings view, transfer form, and transfer history
- Show cash and stock balances on selected accounts in the transfer form to support decision-making
- Add guardrails to existing buy/sell: atomicity, sell validation, price sanity warnings

**Non-Goals:**
- Lot tracking on transfers (individual `StockTransaction` lot records are not moved or split)
- Fixing per-account gains calculations (already imprecise, out of scope)
- Transfers between brokerage accounts (MoneyAccount to MoneyAccount for stock)
- Combined stock-for-cash atomic swap (users perform stock transfer and cash transfer as two separate actions)
- Moving buy/sell functionality to the new stocks page (stays on account detail page)

## Decisions

### 1. Extend `StockTransaction` with a "Transfer" type and `to_shares` FK

`StockTransaction` is used only for display and CRUD -- no production calculations derive from it. Adding a "T" (Transfer) type alongside "B" (Buy) and "S" (Sell), plus a nullable `to_shares` FK to `StockShares`, allows a single record to capture a transfer:

```
StockTransaction (extended)
  existing:
    shares              FK → StockShares (source for transfers)
    transaction_type    "B" / "S" / "T"
    num_shares          DecimalField
    price               DecimalField (market price at time of transfer)
    transaction_date    DateField
    user                FK → User

  new:
    to_shares           FK → StockShares (nullable, destination for transfers)
```

For buys and sells, `to_shares` is null. For transfers, `shares` is the source and `to_shares` is the destination. One record, both sides referenced, no pairing needed.

**Alternatives considered:**
- Separate `StockTransfer` model: Clean separation but adds a new table for what is conceptually another type of stock transaction. Since `StockTransaction` isn't used for calculations, extending it is safe and simpler.
- Paired "TI"/"TO" records: Two records per transfer with no FK linking them. Harder to query transfer history and show "from → to" in one row.

### 2. Transfer operates only on `num_shares`, not on lots

Moving or splitting `StockTransaction` lot records would add significant complexity (partial lot splitting, cost basis recalculation) for limited benefit. The `num_shares` denormalized field is the sole source of truth for all production balance displays. The lot records (`StockTransaction`) stay untouched on the original `StockShares`.

**Trade-off:** Cost basis accuracy per-account degrades after transfers. Accepted because per-account gains are already imprecise (string-matching heuristic on monetary transactions).

### 3. `transaction.atomic()` with `select_for_update()` for transfers

The transfer modifies two `StockShares` records and creates a `StockTransaction`. This must be atomic to prevent partial state. `select_for_update()` on the source `StockShares` prevents race conditions where concurrent transfers both read the same share count.

### 4. No monetary `Transaction` created for stock transfers

Stock transfers are pure re-categorization. No cash changes hands, no brokerage position changes. Creating a $0 monetary transaction would pollute the transaction ledger and confuse account balance calculations that sum `amount_spent`.

### 5. Wrap existing buy/sell in `transaction.atomic()`

The current `create_stock_transaction` view saves a monetary `Transaction`, `BudgetAllocation`, `StockTransaction`, and updates `StockShares.num_shares` with no atomic wrapper. A failure partway through leaves inconsistent state. Wrapping in `transaction.atomic()` is a minimal change that prevents this.

### 6. Reject sells when insufficient shares

Currently the system allows selling more shares than owned (the `more_shares_sold` property exists to detect this after the fact). Adding validation to reject sells where `num_shares > stock_shares.num_shares` prevents data inconsistency at the source.

### 7. Price sanity warning using market price comparison

The `Stock` model already stores `market_price`. When the user-entered price diverges significantly from market price (e.g., ratio < 0.5 or > 2.0), display a warning. This catches the common mistake of swapping the share count and price fields. This is a soft warning (confirmation), not a hard reject, since entering historical prices for past transactions is legitimate.

### 8. New `/stocks/` page rather than extending the account detail page

The account detail page operates in the context of a single account. Stock transfers require a cross-account perspective (selecting source and destination budget accounts). A dedicated stocks page provides the natural home for this cross-account view, with room for a holdings overview and transfer history.

Existing stock displays on the account detail page (holdings, buy/sell, transaction history) remain unchanged, except the query is updated to also match `to_shares` so transfers appear on the destination account's history.

### 9. Account detail query update for transfer visibility

The account detail page queries stock transactions with `StockTransaction.objects.filter(shares__in=all_stock_shares)`. This only matches the source side of transfers. Adding `| Q(to_shares__in=all_stock_shares)` ensures transfers also appear in the destination account's transaction history. The template needs minor updates to display "T" type differently from buys/sells (e.g., "Transfer from X" or "Transfer to X").

### 10. Stocks page lives in the existing `stocks` Django app

The `stocks` app already contains models and views for stock operations. Adding the new page, transfer view, and model changes here keeps stock-related code cohesive. URL routing will be added under `/stocks/`.

## Risks / Trade-offs

- **[Per-account gains become less meaningful after transfers]** -> Accepted. Already imprecise. Could be revisited in a future change that overhauls gains calculation.
- **[`num_shares_owned` computed property diverges from `num_shares` field]** -> `num_shares_owned` aggregates Buy/Sell StockTransactions but not Transfers. This property is unused in production (only tests). Tests may need updating.
- **[No undo for transfers]** -> Users can perform a reverse transfer. The StockTransaction audit trail makes it possible to build an undo feature later.
- **[Concurrent transfer race conditions]** -> Mitigated by `select_for_update()` within `transaction.atomic()`.
- **[Transfer to same account]** -> Validation rejects transfers where source and destination budget accounts are identical.
- **[Price warning false positives]** -> Market prices may be stale (up to 15 min). A soft warning with confirmation avoids blocking legitimate entries.
- **[Nullable `to_shares` FK on all StockTransactions]** -> Null for all existing records and all future buys/sells. Minor schema overhead, no functional impact.
