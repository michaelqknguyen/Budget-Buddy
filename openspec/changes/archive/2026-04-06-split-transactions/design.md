## Context

BudgetBuddy is a Django personal finance app where every transaction is currently tied to exactly one budget account via a direct `Transaction.budget_account` foreign key. Budget account balances are computed by aggregating `Transaction.amount_spent` filtered by `budget_account`. This 1:1 relationship is referenced in 57 locations across models, views, forms, templates, utils, admin, and tests.

Users need to split a single real-world purchase across multiple budget categories. The current workaround — creating multiple fake transactions — breaks statement reconciliation (one credit card line should equal one transaction row) and is error-prone.

The codebase uses Django's standard patterns: function-based views for creation, class-based views for update/delete, crispy forms for the edit page, and inline HTML forms for the account detail page. Balances are 100% aggregated from transactions (no stored balance fields).

## Goals / Non-Goals

**Goals:**
- Allow any transaction to be allocated across one or more budget accounts
- Maintain the invariant: one transaction row = one real-world purchase / statement line
- Ensure allocation amounts always sum exactly to `transaction.amount_spent`
- Provide a simple default experience (single allocation) with opt-in split UI
- Clean migration path from the existing `budget_account` FK with no data loss
- Unified query path for budget balances (no conditional branching for split vs. non-split)

**Non-Goals:**
- Split transactions across money accounts (splits are budget categorization only)
- Recurring/template splits
- Splitting transfer transactions (transfers create paired debit/credit rows, unrelated to budgeting)
- Modifying the `StockShares.budget_account` FK (separate concern, untouched)
- Percentage-based allocation (amounts only, users do their own math)

## Decisions

### 1. BudgetAllocation-only model (no budget_account on Transaction)

**Choice:** Remove `Transaction.budget_account` entirely. All budget associations go through a new `BudgetAllocation` join table. Non-split transactions have exactly 1 allocation row; split transactions have 2+.

**Alternatives considered:**
- *Keep `budget_account` on Transaction + add SplitLine for splits only*: Requires `is_split` branching in every balance query, form save, and display template. Two code paths to maintain indefinitely.
- *Keep `budget_account` as a denormalized cache of the primary allocation*: Risk of desync, still need branching in forms, marginal query savings not worth the complexity.

**Rationale:** One query path (`SUM(budgetallocation.amount)` grouped by budget account) works for all transactions regardless of split count. Cleaner long-term despite the upfront migration cost. Statement reconciliation stays clean (Transaction = statement line).

### 2. BudgetAllocation model schema

```python
class BudgetAllocation(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="allocations")
    budget_account = models.ForeignKey(BudgetAccount, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)
```

**Key choices:**
- `on_delete=DO_NOTHING` for budget_account matches existing Transaction.budget_account behavior (budget accounts are never deleted in practice).
- `related_name="allocations"` for clean reverse access (`transaction.allocations.all()`).
- `description` is optional, useful for labeling portions ("Groceries portion").
- No `created_at`/`updated_at` — allocations are always saved atomically with their transaction, history isn't needed independently.

### 3. Two-phase migration strategy

**Phase 1 (single migration):**
1. Add `BudgetAllocation` model
2. Data migration: `BudgetAllocation.objects.bulk_create()` — one allocation per existing Transaction that has `budget_account` set, copying `budget_account` and `amount_spent`
3. Remove `budget_account` FK from Transaction

**Rationale:** Could be split into three migrations for extra safety, but this is a personal finance app with a single user, not a high-availability production system. A single migration with the backfill keeps the deployment atomic. If needed, can split into add→backfill→remove as three separate migrations.

**Rollback:** Reverse migration re-adds `budget_account` to Transaction and copies back from allocations (only safe if no splits have been created yet, which is acceptable for a personal app).

### 4. Form interaction pattern

**Default (single allocation):** Transaction form looks identical to today — one budget account dropdown, one amount. On save, creates one `BudgetAllocation`.

**Split mode:** "Split" button reveals a Django inline formset. Each row has budget account + amount + optional description. JavaScript validates that amounts sum to the transaction total before submission. Server-side validation enforces the same constraint.

**Edit → split conversion:** User clicks "Split" on an existing single-allocation transaction, the existing allocation pre-fills the first formset row, and they can add more rows (adjusting amounts to still sum to the total).

### 5. Balance query approach

Current: `BudgetAccount.objects.annotate(balance=Sum("transaction__amount_spent"))`

New: `BudgetAccount.objects.annotate(balance=Sum("budgetallocation__amount"))`

This works via Django's reverse FK traversal. The annotation follows `BudgetAccount ← BudgetAllocation.budget_account` then sums `amount`. No join through Transaction needed for budget balances.

Money account balances remain unchanged: `SUM(transaction.amount_spent)` filtered by `money_account`.

### 6. Transaction queries — prefetch instead of select_related

Current `get_transactions()` uses `select_related("budget_account")`. This becomes `prefetch_related("allocations__budget_account")` since allocations are a reverse FK (one-to-many). This is a single extra query (batch prefetch) rather than N+1.

## Risks / Trade-offs

**[57 references to update]** → Methodical file-by-file changes with tests run after each major group. The reference trace is already categorized (balance calcs, filters, creation, templates, forms, tests, admin, migrations).

**[Data migration on existing transactions]** → `bulk_create` backfill is safe for the dataset size. Personal app with hundreds/low-thousands of transactions, not millions. Wrapped in atomic transaction.

**[Formset complexity in templates]** → Django inline formsets require JavaScript for dynamic row add/remove. Keep it simple: vanilla JS, no framework dependency. The existing account.html already has inline JS for AJAX stock prices, so this is consistent.

**[Sum validation precision]** → Decimal arithmetic avoids floating-point issues. `DecimalField(max_digits=10, decimal_places=2)` on both `Transaction.amount_spent` and `BudgetAllocation.amount`. Server-side validation uses `Decimal` comparison, not float.

**[Paycheck contribution flow creates multiple transactions]** → Each paycheck contribution already creates separate Transaction rows per budget account. These continue to work as-is — each Transaction gets one BudgetAllocation. No special handling needed.
