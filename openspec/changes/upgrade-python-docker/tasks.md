## 1. Requirements Upgrade

- [ ] 1.1 Update `requirements/base.txt` — Django 3.2→5.2, allauth 0.51→65+, crispy-forms 1.x→2.x, Pillow 9→11, redis 4→5, whitenoise 6.2→latest, django-environ 0.9→0.11, add yfinance, remove django-utils-six
- [ ] 1.2 Update `requirements/production.txt` — gunicorn 20→23, psycopg2 2.9.3→2.9.9+, sentry-sdk 1→2, fix anymail to use sendgrid extra, remove Collectfast
- [ ] 1.3 Update `requirements/local.txt` — werkzeug 2→3, pytest 7→8, black 22→25, pylint-django latest, django-debug-toolbar latest, django-extensions latest, remove model-mommy (use factory-boy only)
- [ ] 1.4 Remove commented-out DRF and coreapi lines from `requirements/base.txt`
- [ ] 1.5 Update `runtime.txt` from `python-3.9.13` to `python-3.13`

## 2. Django Code Fixes

- [ ] 2.1 Update `config/settings/base.py` — remove `USE_L10N` (always True in Django 5.2), update `LOCALE_PATHS` to use `BASE_DIR / "locale"` path syntax, update `ROOT_DIR` and `APPS_DIR` to use `pathlib` instead of `environ.Path`
- [ ] 2.2 Update allauth settings in `base.py` to v65+ format — add `ACCOUNT_LOGIN_METHODS`, `ACCOUNT_SIGNUP_FIELDS`, verify `ACCOUNT_EMAIL_VERIFICATION` format
- [ ] 2.3 Update `CRISPY_TEMPLATE_PACK` from `"bootstrap4"` to `"bootstrap5"` in `base.py`
- [ ] 2.4 Update `config/settings/production.py` — change `STATICFILES_STORAGE` to `STORAGES` dict format (Django 4.2+), update sentry-sdk init to 2.x format, remove Collectfast configuration
- [ ] 2.5 Update `config/settings/local.py` — fix the dummy DATABASES override to use proper PostgreSQL connection for Docker
- [ ] 2.6 Update `config/settings/test.py` if it exists for Django 5.2 compatibility
- [ ] 2.7 Verify `budgetbuddy/users/adapters.py` compatibility with allauth 65+ (likely no changes needed)
- [ ] 2.8 Run `python manage.py check` to catch any remaining Django 5.2 compatibility issues

## 3. Stock Price Migration to yfinance

- [ ] 3.1 Rewrite `stocks/managers.py` — replace RapidAPI HTTP calls with `yfinance.Ticker()` for price fetching in `StockManager.update_market_prices()`
- [ ] 3.2 Remove `YAHOO_FINANCE_API_HOST`, `YAHOO_FINANCE_QUOTES_URI`, and `RAPID_API_KEY` references from `config/settings/base.py`
- [ ] 3.3 Verify `StockSharesManager.investment_sum()` works with new price fetching
- [ ] 3.4 Test stock transaction flow locally — create a buy, verify price is fetched and shares are updated

## 4. Docker Rebuild

- [ ] 4.1 Create new `Dockerfile` at project root — multi-stage build with Python 3.13-slim-bookworm, wheel caching, non-root user, gunicorn entrypoint
- [ ] 4.2 Create `docker-compose.yml` at project root with services: django, postgres (17), redis (7-alpine), mailpit, adminer
- [ ] 4.3 Create `.envs/.local/.django` template file with local development defaults
- [ ] 4.4 Create `.envs/.local/.postgres` template file with local database credentials
- [ ] 4.5 Update `compose/production/postgres/Dockerfile` to use PostgreSQL 17 and copy maintenance scripts
- [ ] 4.6 Verify `docker compose up` starts all services and Django connects to PostgreSQL and Redis
- [ ] 4.7 Verify migrations run successfully in Docker environment
- [ ] 4.8 Verify the application is accessible at localhost:8000 and all major pages load

## 5. Deployment Configuration

- [ ] 5.1 Update `render.yaml` — change `dockerfilePath` from `Dockerfile.render` to `Dockerfile`, remove `RAPID_API_KEY` env var
- [ ] 5.2 Remove `PAPERTRAIL_API_TOKEN` from render.yaml envVars
- [ ] 5.3 Verify `render.yaml` database and Redis service references are correct
- [ ] 5.4 Test production Dockerfile build locally: `docker build -t budgetbuddy-prod .`

## 6. Cleanup

- [ ] 6.1 Remove `Dockerfile.render` (replaced by `Dockerfile`)
- [ ] 6.2 Remove `local.yml` (replaced by `docker-compose.yml`)
- [ ] 6.3 Remove `compose/local/django/Dockerfile` (replaced by root `Dockerfile`)
- [ ] 6.4 Remove `compose/production/django/Dockerfile` (replaced by root `Dockerfile`)
- [ ] 6.5 Remove `compose/production/traefik/` directory
- [ ] 6.6 Remove `compose/local/docs/` directory
- [ ] 6.7 Remove `budgetbuddy/quickstart/` directory (unused DRF skeleton)
- [ ] 6.8 Remove `REST_FRAMEWORK` settings from `config/settings/base.py`
- [ ] 6.9 Remove `COLLECTFAST_STRATEGY` from `config/settings/base.py`
- [ ] 6.10 Remove Collectfast import and configuration from `config/settings/production.py`
- [ ] 6.11 Remove `django-utils-six` from production requirements (already done in 1.2)

## 7. Verification

- [ ] 7.1 Run `python manage.py check --deploy` and fix any deployment warnings
- [ ] 7.2 Run the test suite: `pytest` — all tests pass
- [ ] 7.3 Test authentication flow — login, logout, password reset, email verification
- [ ] 7.4 Test dashboard page loads with account balances
- [ ] 7.5 Test account CRUD operations — create/edit/delete money and budget accounts
- [ ] 7.6 Test transaction creation and transfers
- [ ] 7.7 Test paycheck recording and budget contributions
- [ ] 7.8 Test stock transaction creation — verify yfinance price fetch works
- [ ] 7.9 Test email delivery — verify emails appear in Mailpit UI
- [ ] 7.10 Run `mypy budgetbuddy` and fix any type errors from Django 5.2 stubs
- [ ] 7.11 Run `black .` and `flake8` to ensure code quality
