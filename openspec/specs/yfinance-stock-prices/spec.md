## ADDED Requirements

### Requirement: Stock prices are fetched via yfinance library
The system SHALL use the `yfinance` library to fetch current market prices for stock tickers, replacing the previous RapidAPI Yahoo Finance integration.

#### Scenario: Fetch price for a single ticker
- **WHEN** `StockManager.update_market_prices()` is called with a list of tickers
- **THEN** each ticker's current market price is retrieved using yfinance and saved to the Stock model

#### Scenario: New ticker price lookup
- **WHEN** a stock transaction is created for a ticker that does not exist in the database
- **THEN** the system creates the Stock record and fetches its market price using yfinance

#### Scenario: Batch price update
- **WHEN** `update_market_prices()` is called with multiple tickers
- **THEN** all tickers are fetched in a single batch operation and their `market_price` and `updated_at` fields are updated

### Requirement: Price caching respects update interval
The system SHALL only refresh stock prices from yfinance if the last update was more than 900 seconds (15 minutes) ago.

#### Scenario: Cached price is used
- **WHEN** `update_market_prices()` is called and a Stock's `updated_at` is less than 900 seconds ago
- **THEN** that Stock's price is NOT re-fetched from yfinance

#### Scenario: Stale price is refreshed
- **WHEN** `update_market_prices()` is called and a Stock's `updated_at` is more than 900 seconds ago
- **THEN** that Stock's price IS re-fetched from yfinance

### Requirement: No RapidAPI dependency for stock prices
The system SHALL NOT require any external API key or RapidAPI configuration for stock price fetching.

#### Scenario: No API key needed
- **WHEN** the application starts without RAPID_API_KEY set
- **THEN** stock price fetching works without error

## REMOVED Requirements

### Requirement: RapidAPI Yahoo Finance integration
**Reason**: Replaced by yfinance library which provides the same data source without API key dependency
**Migration**: Remove `RAPID_API_KEY` environment variable, `YAHOO_FINANCE_API_HOST`, `YAHOO_FINANCE_QUOTES_URI` settings, and all HTTP client code in `stocks/managers.py`
