## ADDED Requirements

### Requirement: Transfer stock shares between budget accounts
The system SHALL allow users to transfer a specified number of shares of a stock from one budget account to another within the same brokerage account. The transfer is recorded as a single `StockTransaction` with `transaction_type="T"`, where `shares` references the source `StockShares` and `to_shares` references the destination `StockShares`. This is a pure re-categorization -- no cash changes hands and no brokerage positions are affected.

#### Scenario: Successful transfer with sufficient shares
- **WHEN** user transfers 7 shares of AAPL from "Car Fund" to "Retirement" and the source StockShares has 15 shares
- **THEN** source StockShares.num_shares is decremented to 8, destination StockShares is created (or updated) with num_shares incremented by 7, and a StockTransaction record is created with transaction_type="T", shares=source, to_shares=destination, price=current market price

#### Scenario: Transfer all shares from source
- **WHEN** user transfers all 15 shares of AAPL from "Car Fund" to "Retirement"
- **THEN** source StockShares.num_shares becomes 0, destination StockShares.num_shares is incremented by 15, and the StockTransaction record is created. The source StockShares record remains in the database.

#### Scenario: Transfer to budget account that already holds the same stock
- **WHEN** user transfers 5 shares of AAPL from "Car Fund" to "Retirement" and "Retirement" already holds 20 shares of AAPL in the same brokerage
- **THEN** destination StockShares.num_shares is incremented from 20 to 25

### Requirement: Validate transfer inputs
The system SHALL reject invalid stock transfers and provide clear error feedback.

#### Scenario: Insufficient shares
- **WHEN** user attempts to transfer 20 shares but source StockShares only has 15
- **THEN** the transfer is rejected with an error indicating insufficient shares

#### Scenario: Zero or negative share count
- **WHEN** user attempts to transfer 0 or a negative number of shares
- **THEN** the transfer is rejected with an error indicating the share count must be positive

#### Scenario: Same source and destination account
- **WHEN** user attempts to transfer shares where the source and destination budget accounts are the same
- **THEN** the transfer is rejected with an error indicating the accounts must be different

### Requirement: Atomic transfer operation
The system SHALL execute the entire transfer (decrement source, increment/create destination, create StockTransaction record) within a single database transaction. If any step fails, all changes SHALL be rolled back.

#### Scenario: Failure during transfer rolls back all changes
- **WHEN** a database error occurs after decrementing the source but before creating the StockTransaction record
- **THEN** the source StockShares.num_shares is unchanged (rolled back to its original value)

#### Scenario: Concurrent transfers are serialized
- **WHEN** two transfers from the same source StockShares are submitted simultaneously
- **THEN** they are processed sequentially via row-level locking, and the second transfer sees the updated share count from the first

### Requirement: Transfer visibility on account detail page
The system SHALL display transfer StockTransactions on both the source and destination account detail pages.

#### Scenario: Transfer appears on source account page
- **WHEN** user views the account detail page for the source budget account
- **THEN** the stock transactions table includes the transfer record, displayed distinctly from buys/sells (e.g., "Transfer to Retirement")

#### Scenario: Transfer appears on destination account page
- **WHEN** user views the account detail page for the destination budget account
- **THEN** the stock transactions table includes the transfer record, displayed distinctly from buys/sells (e.g., "Transfer from Car Fund")
