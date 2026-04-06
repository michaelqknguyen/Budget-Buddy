## Context

BudgetBuddy's account detail view (`account_view` in `accounts/views.py`) has three performance issues:

1. **Synchronous stock price fetching in views**: `calculate_investment_balance()` calls `Stock.objects.update_market_prices()`, which makes sequential HTTP requests to Yahoo Finance (one per stale ticker, 10s timeout each). This blocks page rendering for seconds.

2. **Duplicate function call**: `calculate_investment_balance(all_stock_shares)` is called at line 187 (stored in a variable) and again at line 201 (in the context dict), doubling the aggregate query and potentially triggering `update_market_prices()` twice.

3. **Missing database index**: `Transaction.transaction_date` is used in `__range` filters on every account detail page load but has no database index, causing full table scans.

The app uses Django 5.2, PostgreSQL 17, and Redis 7 (via Docker Compose locally, Render in production).

## Goals / Non-Goals

**Goals:**
- Pages load without blocking on external HTTP requests
- Stock prices still update automatically (within ~15 minutes of staleness)
- Eliminate redundant database queries from duplicate function calls
- Date-range queries on transactions use an index

**Non-Goals:**
- Real-time stock price streaming / websockets
- Celery or any new task queue dependency -- keep it simple
- Fixing the N+1 query issues (select_related, investment_sum property) -- separate change
- Changing the 15-minute staleness interval

## Decisions

### 1. AJAX endpoint for stock price updates

**Decision**: Add a Django view endpoint (e.g., `/budget/api/update-stock-prices/`) that calls `update_market_prices()` and returns updated investment balances as JSON. The account detail template fires this via `fetch()` after the page loads.

**Rationale**: This is the simplest approach with no new dependencies. The page renders immediately with the last-known prices. JS fires the update in the background, and if prices changed, updates the displayed values.

**Alternatives considered**:
- *Celery periodic task*: Adds a dependency (Celery worker process, beat scheduler). Overkill for a single-user app.
- *Django management command + cron*: Works but prices would only update on the cron schedule, not when the user is actively viewing the page. Also, Render's cron jobs are a paid add-on.
- *Redis cache with TTL*: Still need something to populate the cache; doesn't solve the "who triggers the fetch" problem.

### 2. Remove `update_market_prices()` from `calculate_investment_balance()`

**Decision**: `calculate_investment_balance()` becomes a pure read function -- it only aggregates share values from the database. The AJAX endpoint is the sole trigger for `update_market_prices()`.

**Rationale**: A function called `calculate_investment_balance` should not have the side effect of making HTTP calls. Separating read from write makes the code predictable and testable.

### 3. Reuse computed variable instead of duplicate call

**Decision**: Replace `calculate_investment_balance(all_stock_shares)` at line 201 with the `investment_balance` variable already computed at line 187.

**Rationale**: One-line fix, no behavior change.

### 4. Add `db_index=True` to `Transaction.transaction_date`

**Decision**: Add `db_index=True` to the `transaction_date` field on the `Transaction` model and generate a migration.

**Rationale**: This field is used in `__range` filters on every account detail page. Django auto-indexes ForeignKey fields but not regular fields. The index is small (one B-tree on a date column) and speeds up all date-range queries.

### 5. AJAX endpoint scope and auth

**Decision**: The endpoint is `@login_required`, accepts POST only, filters stocks by the requesting user's shares, and returns JSON with updated balances per account. It reuses the existing `update_market_prices()` manager method.

**Rationale**: No new auth mechanism needed. POST-only prevents CSRF issues with GET caching. User-scoped filtering ensures one user can't trigger updates for another's stocks.

## Risks / Trade-offs

- **[Stale prices on initial render]** → Users see last-known prices until AJAX completes. Mitigation: Show a subtle loading indicator on investment balance values; update typically completes in 1-3 seconds.
- **[AJAX failure]** → If Yahoo is down or rate-limited, prices stay stale. Mitigation: This is the same failure mode as today, just non-blocking. The endpoint returns the current DB values regardless.
- **[No background updates when user isn't on the page]** → Prices only refresh when someone views the page. Mitigation: Acceptable for a single-user personal finance app. If needed later, a management command + cron can be added independently.
