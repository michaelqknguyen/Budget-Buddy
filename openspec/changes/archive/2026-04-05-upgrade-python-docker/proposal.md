## Why

Python 3.9 reached EOL in October 2025 and no longer receives security patches. The current Django 3.2 LTS also reached EOL in April 2024. Running on unsupported versions means no security fixes, no compatibility with modern packages, and growing deployment risk.

Additionally, the local Docker setup is incomplete — missing Redis, email testing, and database admin tools — making it unsuitable as a standalone development or self-hosted environment.

## What Changes

- **Python 3.9 → 3.13**: Upgrade the base Python version across all Dockerfiles
- **Django 3.2 → 5.2**: Upgrade to the latest Django LTS (supported until 2028)
- **All dependencies**: Bump every package to versions compatible with Python 3.13 and Django 5.2
- **Docker setup**: Replace the existing compose/local/django Dockerfile and local.yml with a clean, self-contained Dockerfile and docker-compose.yml that includes Django, PostgreSQL, Redis, Mailpit (email testing), and Adminer (database admin)
- **Production Dockerfile**: Replace the Render buildpack-based Dockerfile.render with a standard multi-stage Dockerfile that works for both local and Render deployment
- **Stock price fetching**: Replace RapidAPI Yahoo Finance integration with `yfinance` library (no API key needed, same data source)
- **Settings cleanup**: Remove deprecated Django settings, update allauth configuration to new format, fix SendGrid dependency specification
- **Remove dead code**: Remove unused DRF/quickstart skeleton, Collectfast, django-utils-six, Papertrail integration

## Capabilities

### New Capabilities
- `local-docker-environment`: Complete local Docker Compose setup with PostgreSQL, Redis, Mailpit, and Adminer for self-contained development and self-hosted deployment
- `yfinance-stock-prices`: Stock price fetching via yfinance library instead of external RapidAPI service

### Modified Capabilities
- `authentication`: Allauth settings updated to v65+ format; adapter compatibility maintained
- `deployment`: Production Dockerfile changed from buildpack-based to standard multi-stage; render.yaml updated to point at new Dockerfile

## Impact

- **All Python files**: Django 3.2 → 5.2 breaking changes (url() removal, deprecated APIs, allauth settings)
- **All Dockerfiles**: New base image (python:3.13-slim-bookworm), updated build steps
- **requirements/*.txt**: Every dependency version changes
- **config/settings/*.py**: Settings structure changes for allauth, crispy-forms, deprecated settings removal
- **render.yaml**: Updated to reference new Dockerfile, remove RAPID_API_KEY env var
- **BudgetBuddy/stocks/views.py and managers.py**: Stock price fetching logic changes from API calls to yfinance
- **BudgetBuddy/users/adapters.py**: Minimal changes, likely compatible as-is
- **Users**: No user-facing changes expected; this is an infrastructure upgrade
