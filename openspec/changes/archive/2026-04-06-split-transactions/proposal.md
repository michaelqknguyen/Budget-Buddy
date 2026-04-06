## Why

Users sometimes make a single purchase that should be categorized across multiple budget accounts — for example, a $150 Costco run that is $80 groceries, $40 household supplies, and $30 clothing. Currently, each transaction can only be assigned to one budget account, forcing users to either pick a single category (inaccurate budgeting) or manually create multiple fake transactions (error-prone and breaks statement reconciliation). Split transactions solve this by letting users allocate a single transaction's amount across multiple budget accounts.

## What Changes

- **New `BudgetAllocation` model** that links transactions to budget accounts with per-allocation amounts and optional descriptions. Replaces the direct `budget_account` FK on `Transaction`.
- **BREAKING**: Remove `budget_account` foreign key from the `Transaction` model. All budget account associations move to `BudgetAllocation` rows. A data migration backfills one `BudgetAllocation` per existing transaction.
- **Updated transaction forms** — the default create/edit form shows a single budget account (as today). A "Split" button expands an inline formset for multiple allocations with amounts that must sum to the transaction total.
- **Updated balance calculations** — budget account balances change from `SUM(transaction.amount_spent)` filtered by `budget_account` to `SUM(budgetallocation.amount)` grouped by budget account.
- **Updated transaction display** — the transaction table shows multiple budget account tags when a transaction is split.
- **Validation constraints** — allocation amounts must sum exactly to `transaction.amount_spent`. Enforced at model, form, and database levels.

## Capabilities

### New Capabilities
- `split-transactions`: Ability to allocate a single transaction's amount across multiple budget accounts, including the BudgetAllocation model, form interactions, validation rules, and display behavior.

### Modified Capabilities
<!-- No existing spec-level requirements are changing. The async-stock-prices endpoint
     returns investment_balance which is money-account-based, unaffected by this change.
     Budget balance query path changes are implementation details, not requirement changes. -->

## Impact

- **Models**: `Transaction` loses `budget_account` FK; new `BudgetAllocation` model added to `accounts/models.py`
- **Migrations**: Two migrations — one to add `BudgetAllocation` and backfill data, one to remove `budget_account` from `Transaction`
- **Views**: `accounts/views.py` (create, update, delete, account_view, index), `pages/views.py` (home), `paychecks/views.py` (paycheck contribution flow), `stocks/views.py` (stock transactions)
- **Forms**: `accounts/forms.py` (TransactionForm), `paychecks/forms.py` (TransactionPaystubForm), `stocks/forms.py` — all must create `BudgetAllocation` rows instead of setting `budget_account`
- **Templates**: `account.html` (inline form + transaction table), `transaction_form.html` (edit form), `accounts.html` (overview balances), `paystub_create.html`
- **Utils**: `accounts/utils.py` `get_transactions()` must prefetch allocations instead of select_related on budget_account
- **Admin**: `TransactionAdmin` display and inline for allocations
- **Tests**: ~13 test locations across accounts, stocks, paychecks, and pages need updates to create `BudgetAllocation` objects instead of setting `budget_account`
- **57 total references** to `Transaction.budget_account` across the codebase need updating
