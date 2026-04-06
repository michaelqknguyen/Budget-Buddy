## MODIFIED Requirements

### Requirement: Price caching respects update interval
The system SHALL only refresh stock prices from Yahoo Finance if the last update was more than 900 seconds (15 minutes) ago. Price updates SHALL be triggered by the dedicated AJAX endpoint, not by balance calculation functions.

#### Scenario: Cached price is used
- **WHEN** `update_market_prices()` is called and a Stock's `updated_at` is less than 900 seconds ago
- **THEN** that Stock's price is NOT re-fetched from Yahoo Finance

#### Scenario: Stale price is refreshed
- **WHEN** `update_market_prices()` is called and a Stock's `updated_at` is more than 900 seconds ago
- **THEN** that Stock's price IS re-fetched from Yahoo Finance

#### Scenario: Balance calculation does not trigger price updates
- **WHEN** `calculate_investment_balance()` is called from a view or utility function
- **THEN** it SHALL NOT call `update_market_prices()` and SHALL only read existing prices from the database
