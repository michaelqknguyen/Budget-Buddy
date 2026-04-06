### Requirement: Stock prices update asynchronously via AJAX
The system SHALL provide an AJAX endpoint that triggers stock price updates without blocking the page render. The endpoint SHALL be accessible only to authenticated users.

#### Scenario: Page loads with last-known prices
- **WHEN** a user loads an account detail page that displays investment balances
- **THEN** the page renders immediately using the last-known stock prices from the database, without making any HTTP requests to Yahoo Finance during the view

#### Scenario: AJAX triggers background price update
- **WHEN** the account detail page finishes loading
- **THEN** JavaScript SHALL send a POST request to the stock price update endpoint, which fetches fresh prices from Yahoo Finance and returns updated investment balance values as JSON

#### Scenario: Page updates with fresh prices
- **WHEN** the AJAX stock price update returns successfully with new price data
- **THEN** the displayed investment balance values on the page SHALL update to reflect the new prices without a full page reload

#### Scenario: AJAX update fails gracefully
- **WHEN** the AJAX stock price update fails (network error, Yahoo rate limit, timeout)
- **THEN** the page SHALL continue displaying the last-known prices with no error shown to the user

### Requirement: Stock price update endpoint is authenticated
The stock price update endpoint SHALL require authentication and SHALL only update prices for stocks held by the requesting user.

#### Scenario: Unauthenticated request is rejected
- **WHEN** an unauthenticated request is made to the stock price update endpoint
- **THEN** the system SHALL return a 302 redirect to the login page

#### Scenario: User-scoped price updates
- **WHEN** an authenticated user triggers a stock price update
- **THEN** only stocks associated with that user's stock shares SHALL be considered for price updates

### Requirement: Transaction date field is indexed
The `Transaction.transaction_date` field SHALL have a database index to optimize date-range queries.

#### Scenario: Date range query uses index
- **WHEN** transactions are filtered by `transaction_date__range`
- **THEN** the query SHALL use a B-tree index on the `transaction_date` column

### Requirement: No duplicate investment balance calculation
The `account_view` function SHALL compute `calculate_investment_balance()` exactly once per request and reuse the result.

#### Scenario: Single calculation per request
- **WHEN** the account detail view is rendered
- **THEN** `calculate_investment_balance()` SHALL be called once, and its return value SHALL be used for both the `potential_gain` computation and the template context

### Requirement: calculate_investment_balance is a pure read
The `calculate_investment_balance()` function SHALL only aggregate share values from the database. It SHALL NOT trigger any external HTTP requests or side effects.

#### Scenario: No HTTP calls during balance calculation
- **WHEN** `calculate_investment_balance()` is called
- **THEN** it SHALL only execute a database aggregate query and SHALL NOT call `update_market_prices()` or any external API
