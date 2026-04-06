## 1. Model and Migration

- [x] 1.1 Add `BudgetAllocation` model to `accounts/models.py` with `transaction` FK (CASCADE), `budget_account` FK (DO_NOTHING), `amount` DecimalField, and `description` CharField
- [x] 1.2 Create migration: add `BudgetAllocation` table, run data migration to backfill one allocation per existing Transaction with `budget_account` set, then remove `budget_account` FK from `Transaction`
- [x] 1.3 Register `BudgetAllocation` in `accounts/admin.py` as an inline on `TransactionAdmin`

## 2. Balance Calculations

- [x] 2.1 Update budget account balance annotations in `accounts/views.py` (`index` and `account_view`) to use `Sum("budgetallocation__amount")` instead of `Sum("transaction__amount_spent")`
- [x] 2.2 Update budget account balance annotations in `pages/views.py` (home page) to use `Sum("budgetallocation__amount")`

## 3. Transaction Queries and Utils

- [x] 3.1 Update `get_transactions()` in `accounts/utils.py` to use `prefetch_related("allocations__budget_account")` instead of `select_related("budget_account")`, and remove `budget_account` filter (replace with allocation-based filter)
- [x] 3.2 Update transaction filtering by budget account in `paychecks/views.py` to filter via `allocations__budget_account` instead of direct `budget_account`

## 4. Forms

- [x] 4.1 Update `TransactionForm` in `accounts/forms.py` — remove `budget_account` field, add `BudgetAllocationFormSet` (inline formset for BudgetAllocation) with budget_account, amount, and description fields
- [x] 4.2 Add form validation to `BudgetAllocationFormSet`: allocation amounts must sum to `transaction.amount_spent`, at least one allocation required
- [x] 4.3 Update `TransactionPaystubForm` in `paychecks/forms.py` — replace `budget_account` field with allocation creation on save
- [x] 4.4 Update stock transaction form in `stocks/forms.py` — replace `budget_account` field with allocation creation on save

## 5. Views — Transaction Create/Update/Delete

- [x] 5.1 Update `create_transaction` in `accounts/views.py` to save `BudgetAllocationFormSet` atomically with the transaction
- [x] 5.2 Update `TransactionUpdateView` in `accounts/views.py` to load and save allocations via the formset
- [x] 5.3 Verify `TransactionDeleteView` cascades allocation deletion (no code change expected, just verify)
- [x] 5.4 Update `transfer_transaction` in `accounts/views.py` — transfers don't use budget accounts, verify no allocation is created
- [x] 5.5 Update paycheck contribution flow in `paychecks/views.py` to create `BudgetAllocation` rows instead of setting `transaction.budget_account`
- [x] 5.6 Update `create_stock_transaction` in `stocks/views.py` to create `BudgetAllocation` instead of setting `transaction.budget_account`

## 6. Templates

- [x] 6.1 Update `account.html` inline transaction form — default single budget account dropdown, "Split" button to reveal formset rows with budget account + amount + description
- [x] 6.2 Add client-side JavaScript in `account.html` for dynamic formset row add/remove and running sum validation
- [x] 6.3 Update `account.html` transaction table to display allocation budget accounts (show multiple tags for split transactions)
- [x] 6.4 Update `transaction_form.html` (edit page) to render the allocation formset with split/unsplit support
- [x] 6.5 Update `paystub_create.html` to use allocation-based budget account field
- [x] 6.6 Verify `accounts.html` overview page displays correct budget balances (driven by view annotation changes in task 2.1)

## 7. Model Validation

- [x] 7.1 Add `clean()` method to `BudgetAllocation` or a custom manager method that validates allocations sum to `transaction.amount_spent`
- [x] 7.2 Ensure atomic saves — transaction + allocations saved within `transaction.atomic()` in all create/update paths

## 8. Tests

- [x] 8.1 Update `TransactionFactory` in `accounts/tests/factories.py` — add `BudgetAllocationFactory`, remove `budget_account` from `TransactionFactory`
- [x] 8.2 Update `accounts/tests/test_forms.py` — test single allocation creation, split allocation creation, sum validation failure
- [x] 8.3 Update `pages/tests/test_views.py` — create `BudgetAllocation` objects instead of setting `transaction.budget_account`
- [x] 8.4 Update `paychecks/tests/test_forms.py` — adjust `TransactionPaystubForm` tests for allocation-based budget account
- [x] 8.5 Update `stocks/tests/factories.py` and `stocks/tests/test_models.py` — `StockShares.budget_account` is unchanged but verify transaction tests use allocations
- [x] 8.6 Add new tests: split transaction create, edit single→split, edit split→single, delete cascades allocations, budget balance with splits
- [x] 8.7 Run full test suite and fix any remaining failures
