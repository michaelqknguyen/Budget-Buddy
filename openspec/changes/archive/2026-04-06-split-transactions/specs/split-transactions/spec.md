## ADDED Requirements

### Requirement: BudgetAllocation model links transactions to budget accounts
The system SHALL use a `BudgetAllocation` model to associate transactions with budget accounts. Each `BudgetAllocation` record SHALL contain a reference to one transaction, one budget account, a decimal amount, and an optional text description. The `Transaction` model SHALL NOT have a direct foreign key to budget account.

#### Scenario: Non-split transaction has one allocation
- **WHEN** a user creates a transaction with a single budget account
- **THEN** the system creates exactly one `BudgetAllocation` row linking that transaction to the selected budget account with the full transaction amount

#### Scenario: Split transaction has multiple allocations
- **WHEN** a user creates a transaction and splits it across multiple budget accounts
- **THEN** the system creates one `BudgetAllocation` row per budget account, each with its respective portion of the total amount

#### Scenario: Transaction deletion cascades to allocations
- **WHEN** a user deletes a transaction
- **THEN** all associated `BudgetAllocation` rows SHALL be deleted automatically

### Requirement: Allocation amounts must sum to transaction total
The system SHALL enforce that the sum of all `BudgetAllocation.amount` values for a given transaction equals `transaction.amount_spent` exactly. This constraint SHALL be enforced at both form validation and model validation levels.

#### Scenario: Valid allocation sum accepted
- **WHEN** a user submits a transaction with allocations summing to the transaction's `amount_spent`
- **THEN** the system saves the transaction and all allocations successfully

#### Scenario: Invalid allocation sum rejected
- **WHEN** a user submits a transaction with allocations that do not sum to the transaction's `amount_spent`
- **THEN** the system rejects the submission and displays a validation error indicating the mismatch

#### Scenario: Single allocation inherits full amount
- **WHEN** a user submits a transaction without splitting (single budget account selected)
- **THEN** the system creates one allocation with `amount` equal to `transaction.amount_spent`

### Requirement: Transaction form supports single and split modes
The transaction creation and edit forms SHALL default to a single budget account selection (matching current behavior). The form SHALL provide a mechanism to switch to split mode, where the user can add multiple allocation rows, each with a budget account, amount, and optional description.

#### Scenario: Default form shows single budget account
- **WHEN** a user opens the transaction creation form
- **THEN** the form displays a single budget account dropdown and the transaction amount field, with no split UI visible

#### Scenario: User activates split mode
- **WHEN** a user clicks the "Split" control on the transaction form
- **THEN** the form expands to show an inline formset with rows for budget account, amount, and description, pre-populated with the current budget account and full amount in the first row

#### Scenario: User adds allocation rows in split mode
- **WHEN** a user is in split mode and adds a new allocation row
- **THEN** a new empty row appears with budget account dropdown, amount field, and description field

#### Scenario: User removes an allocation row in split mode
- **WHEN** a user removes an allocation row from the split formset (and at least one row remains)
- **THEN** the row is removed and the remaining allocations are preserved

#### Scenario: Client-side sum validation
- **WHEN** the user modifies allocation amounts in split mode
- **THEN** the form displays a running total of allocations and indicates whether it matches the transaction amount before submission

### Requirement: Editing a transaction preserves or modifies allocations
The transaction edit form SHALL load existing allocations for display and editing. Users SHALL be able to convert a single-allocation transaction into a split transaction and vice versa.

#### Scenario: Edit form loads existing allocations
- **WHEN** a user opens the edit form for a transaction with existing allocations
- **THEN** the form displays all current allocations with their budget account, amount, and description values

#### Scenario: Convert single allocation to split
- **WHEN** a user edits a single-allocation transaction and activates split mode
- **THEN** the existing allocation appears as the first row and the user can add additional rows, adjusting amounts to maintain the sum constraint

#### Scenario: Convert split back to single allocation
- **WHEN** a user edits a split transaction and removes all but one allocation row
- **THEN** the remaining allocation's amount SHALL equal the transaction total

### Requirement: Budget account balances are computed from allocations
Budget account balances SHALL be computed by summing `BudgetAllocation.amount` values grouped by budget account. This replaces the previous computation that summed `Transaction.amount_spent` filtered by `Transaction.budget_account`.

#### Scenario: Budget balance reflects single-allocation transactions
- **WHEN** the system calculates a budget account's balance
- **THEN** it includes the `amount` from every `BudgetAllocation` linked to that budget account

#### Scenario: Budget balance reflects split transactions
- **WHEN** a transaction is split across budget accounts A and B
- **THEN** budget account A's balance includes only the allocation amount assigned to A, and budget account B's balance includes only the allocation amount assigned to B

#### Scenario: Money account balance is unaffected by allocations
- **WHEN** the system calculates a money account's balance
- **THEN** it sums `Transaction.amount_spent` for that money account (unchanged from current behavior)

### Requirement: Transaction display shows allocation details
When displaying transactions, the system SHALL show the associated budget account(s). For split transactions, the display SHALL indicate that the transaction is split and show the individual allocation details.

#### Scenario: Single-allocation transaction display
- **WHEN** the transaction table displays a transaction with one allocation
- **THEN** it shows the budget account name (matching current display behavior)

#### Scenario: Split transaction display
- **WHEN** the transaction table displays a transaction with multiple allocations
- **THEN** it shows all budget account names with their respective amounts

### Requirement: Data migration from direct FK to allocations
The system SHALL migrate existing transaction data from the `Transaction.budget_account` foreign key to `BudgetAllocation` rows. Every existing transaction that has a `budget_account` set SHALL have exactly one `BudgetAllocation` created with the transaction's `amount_spent` as the allocation amount.

#### Scenario: Existing transaction with budget account is migrated
- **WHEN** the data migration runs on an existing transaction that has `budget_account` set
- **THEN** one `BudgetAllocation` row is created with `amount = transaction.amount_spent` and `budget_account = transaction.budget_account`

#### Scenario: Existing transaction without budget account is skipped
- **WHEN** the data migration runs on an existing transaction that has no `budget_account` set
- **THEN** no `BudgetAllocation` row is created for that transaction

#### Scenario: Migration is atomic
- **WHEN** the data migration executes
- **THEN** all backfill operations complete within a single database transaction, ensuring no partial state

### Requirement: Paycheck and stock transaction flows create allocations
Transaction creation flows in paychecks and stocks modules SHALL create `BudgetAllocation` rows instead of setting `Transaction.budget_account`. These flows always create single-allocation transactions (no splitting in these contexts).

#### Scenario: Paycheck contribution creates allocation
- **WHEN** the paycheck system creates a transaction for a budget account contribution
- **THEN** it creates a `BudgetAllocation` linking the transaction to the budget account with the contribution amount

#### Scenario: Stock transaction creates allocation
- **WHEN** the stock system creates a transaction for a stock purchase or sale
- **THEN** it creates a `BudgetAllocation` linking the transaction to the selected budget account with the transaction amount
