## ADDED Requirements

### Requirement: Stocks overview page
The system SHALL provide a dedicated stocks page at `/stocks/` displaying all stock holdings across all accounts for the authenticated user.

#### Scenario: User views all holdings
- **WHEN** user navigates to `/stocks/`
- **THEN** the page displays a table of all StockShares records with num_shares > 0, showing ticker, number of shares, current market value, budget account name, and brokerage account name

#### Scenario: User with no stock holdings
- **WHEN** user navigates to `/stocks/` and has no StockShares with num_shares > 0
- **THEN** the page displays an empty state indicating no stock holdings

### Requirement: Stock transfer form
The system SHALL provide a form on the stocks page for transferring shares between budget accounts.

#### Scenario: User initiates a transfer
- **WHEN** user selects a source budget account, a stock, a destination budget account, and enters a number of shares, then submits the form
- **THEN** the transfer is executed per the stock-transfers spec and the user is redirected back to the stocks page with a success indication

#### Scenario: Transfer form shows account balances
- **WHEN** user selects a source and destination budget account in the transfer form
- **THEN** the form displays the cash balance (sum of BudgetAllocations) and stock value (investment_sum) for both selected accounts

#### Scenario: Transfer form shows available shares
- **WHEN** user selects a source budget account and a stock in the transfer form
- **THEN** the form displays the number of shares available to transfer for that stock in that budget account

#### Scenario: Transfer validation error
- **WHEN** user submits a transfer that fails validation (per stock-transfers spec)
- **THEN** the form re-displays with the error message and the user's previously entered values preserved

### Requirement: Transfer history
The system SHALL display a history of stock transfers on the stocks page.

#### Scenario: User views transfer history
- **WHEN** user navigates to the stocks page and has completed transfers
- **THEN** the page displays a list of StockTransfer records showing date, stock ticker, number of shares, source budget account, destination budget account, and value at time of transfer (num_shares * price_at_transfer)

#### Scenario: No transfer history
- **WHEN** user navigates to the stocks page and has no StockTransfer records
- **THEN** the transfer history section is either hidden or shows an empty state

### Requirement: Stocks page requires authentication
The system SHALL require the user to be logged in to access the stocks page.

#### Scenario: Unauthenticated access
- **WHEN** an unauthenticated user attempts to access `/stocks/`
- **THEN** they are redirected to the login page

### Requirement: Stocks page in site navigation
The system SHALL include a link to the stocks page in the site navigation.

#### Scenario: Navigation link visible
- **WHEN** an authenticated user views any page
- **THEN** the site navigation includes a link to the stocks page
