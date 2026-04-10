## ADDED Requirements

### Requirement: Atomic buy/sell operations
The system SHALL wrap the entire stock buy/sell flow (creating monetary Transaction, BudgetAllocation, StockTransaction, and updating StockShares.num_shares) in a single database transaction. If any step fails, all changes SHALL be rolled back.

#### Scenario: Failure during buy rolls back all changes
- **WHEN** a database error occurs after creating the monetary Transaction but before saving the StockTransaction
- **THEN** no monetary Transaction, BudgetAllocation, or StockTransaction is persisted, and StockShares.num_shares is unchanged

### Requirement: Reject sells with insufficient shares
The system SHALL reject sell transactions when the number of shares to sell exceeds the current StockShares.num_shares.

#### Scenario: Sell rejected for insufficient shares
- **WHEN** user attempts to sell 20 shares but StockShares.num_shares is 15
- **THEN** the transaction is rejected with an error indicating insufficient shares, and no records are created or modified

#### Scenario: Sell allowed with exact shares
- **WHEN** user attempts to sell 15 shares and StockShares.num_shares is 15
- **THEN** the transaction is accepted, StockShares.num_shares becomes 0

### Requirement: Price sanity warning
The system SHALL warn the user when the entered price per share diverges significantly from the stock's current market price. This is a soft warning requiring confirmation, not a hard rejection.

#### Scenario: Price significantly below market price
- **WHEN** user enters a price that is less than 50% of the current market price (e.g., enters $10 when market price is $150)
- **THEN** the system displays a warning indicating the entered price differs significantly from the market price and asks for confirmation before proceeding

#### Scenario: Price significantly above market price
- **WHEN** user enters a price that is more than 200% of the current market price (e.g., enters $400 when market price is $150)
- **THEN** the system displays a warning indicating the entered price differs significantly from the market price and asks for confirmation before proceeding

#### Scenario: Price within acceptable range
- **WHEN** user enters a price that is between 50% and 200% of the current market price
- **THEN** the transaction proceeds without a warning

#### Scenario: No market price available
- **WHEN** user enters a price for a stock that has no market_price set (null)
- **THEN** the transaction proceeds without a price warning
