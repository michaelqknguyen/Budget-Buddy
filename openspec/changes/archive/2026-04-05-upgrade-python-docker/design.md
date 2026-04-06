## Context

BudgetBuddy is a personal finance / envelope-budgeting app built on Django 3.2.14 with Python 3.9.13. It runs on Render using a buildpack-based Dockerfile.render, with managed PostgreSQL and Redis services. The local development setup uses docker-compose but is incomplete (missing Redis, email testing, database admin).

The codebase is clean — all URL patterns already use modern `path()`, no `url()` calls exist. Custom allauth adapters are minimal (registration toggle only). The app has 4 domain modules: accounts (core), paychecks, stocks, pages.

## Goals / Non-Goals

**Goals:**
- Python 3.13 + Django 5.2 LTS as the new baseline
- All dependencies updated to compatible versions
- Single Dockerfile that works for both local dev and Render deployment
- Full local Docker Compose stack: Django, PostgreSQL, Redis, Mailpit, Adminer
- Replace RapidAPI stock lookups with yfinance (no API key)
- Remove dead dependencies and unused code
- Production deployment to Render continues to work

**Non-Goals:**
- No user-facing feature changes
- No database schema changes (beyond what Django migrations handle)
- No migration to cookiecutter-django template
- No Celery, no Traefik, no AWS S3 — keep the current architecture
- No changes to the business logic in accounts, paychecks, or stocks

## Decisions

### 1. Django 5.2 LTS (not 5.1)
**Decision:** Target Django 5.2, the latest LTS (supported until April 2028).
**Rationale:** Longer support window, Python 3.13 support is native, and since we're doing a full refresh anyway, might as well go to the newest LTS.
**Alternatives considered:** Django 5.1 — more battle-tested but EOL sooner (Dec 2025). Not worth the shorter runway.

### 2. Single Dockerfile for local + production
**Decision:** One multi-stage Dockerfile (`Dockerfile`) used by both docker-compose and Render.
**Rationale:** Eliminates the current split between `Dockerfile.render` (buildpacks) and `compose/local/django/Dockerfile`. Simpler to maintain, identical behavior everywhere.
**Structure:**
```
Stage 1: python-build   — install apt deps, build wheels from requirements
Stage 2: python-run     — copy wheels, install, copy app code, set permissions
```
Render's `render.yaml` will point at this Dockerfile directly (no buildpacks).

### 3. docker-compose.yml replaces local.yml
**Decision:** A single `docker-compose.yml` at the project root replaces `local.yml`.
**Services:**
| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| django | built from Dockerfile | 8000 | Django dev server |
| postgres | postgres:17 | 5432 | Database |
| redis | redis:7-alpine | 6379 | Cache/sessions |
| mailpit | axllent/mailpit | 8025 | Email testing UI |
| adminer | adminer:latest | 8080 | Database admin UI |

**Rationale:** Mailpit is the modern replacement for Mailhog (actively maintained, single binary). Adminer is lighter than pgAdmin (single PHP file, no extra config).

### 4. yfinance replaces RapidAPI
**Decision:** Use `yfinance` library for stock price lookups.
**Rationale:** No API key, no rate limits, no external service dependency. Same Yahoo Finance data source. Eliminates `RAPID_API_KEY` env var entirely.
**Migration:** Replace `stocks/managers.py` HTTP calls with `yfinance.Ticker()` calls. The `Stock.update_market_prices()` method signature stays the same — callers don't need to change.

### 5. Deprecation cleanup
**Decision:** Remove all unused dependencies and dead code in the same change.
**What gets removed:**
- `djangorestframework` / `coreapi` (commented out, never used)
- `Collectfast` (only useful with S3, we use WhiteNoise)
- `django-utils-six` (Python 2/3 compatibility shim, not needed)
- `budgetbuddy/quickstart/` (DRF skeleton, never wired up)
- `PAPERTRAIL_API_TOKEN` env var (Render has built-in logs)
- `compose/production/traefik/` (not used in local or Render)
- `compose/local/docs/` (Sphinx docs container, rarely used)

**What stays:**
- `Dockerfile.render` — kept but simplified to just `FROM ./Dockerfile` or removed entirely in favor of pointing render.yaml at the main Dockerfile
- `render.yaml` — updated to point at new Dockerfile, remove RAPID_API_KEY

### 6. Allauth settings migration
**Decision:** Update to allauth 65+ settings format.
**Key changes:**
- `ACCOUNT_EMAIL_VERIFICATION` → stays the same
- Social account settings move to `SOCIALACCOUNT_*` prefix (already done in current code)
- `ACCOUNT_ADAPTER` and `SOCIALACCOUNT_ADAPTER` → stay the same, signatures unchanged
- New in allauth 65+: `ACCOUNT_LOGIN_METHODS`, `ACCOUNT_SIGNUP_FIELDS` — add these explicitly

### 7. Crispy forms: Bootstrap 4 → Bootstrap 5
**Decision:** Upgrade `crispy-bootstrap5` alongside the crispy-forms 2.x upgrade.
**Rationale:** `crispy-forms` 2.x dropped the built-in Bootstrap 4 template pack. The project already has `crispy-bootstrap5==0.6` installed. Just need to update `CRISPY_TEMPLATE_PACK = "bootstrap5"` and verify templates render correctly.

### 8. psycopg2 → psycopg (v3)
**Decision:** Keep `psycopg2` for now (binary wheel works fine on Python 3.13).
**Rationale:** `psycopg` v3 is the new version but requires code changes (different import paths, different cursor behavior). Not worth the risk in an infrastructure upgrade. Just bump `psycopg2` to latest 2.9.x.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Django 5.2 breaks existing views** — subtle behavior changes in querysets, template rendering, or form handling | Test all major flows after upgrade: dashboard, account views, transaction creation, paycheck recording, stock buys |
| **Allauth 65+ has unexpected breaking changes** beyond settings — email templates, URL patterns, or redirect behavior | Test login, signup, password reset, email verification flows. Allauth changelog is well-maintained. |
| **yfinance rate limiting** — Yahoo may throttle requests if stock prices are fetched too frequently | The existing 15-minute cache (`updated_at` check in `StockManager`) already limits calls. yfinance respects the same constraints. |
| **Bootstrap 5 template changes** — some Bootstrap 4 classes removed/renamed in Bootstrap 5 | Visual regression test all pages. Most changes are minor (e.g., `ml-*` → `ms-*`, `mr-*` → `me-*`). |
| **Render deployment breakage** — new Dockerfile may behave differently than buildpack-based one | Test locally first, then deploy to Render. Keep old `Dockerfile.render` in git until new one is confirmed working. |
| **PostgreSQL 14 → 17 migration** — if running local Postgres 14, volume data may not be compatible | Local dev data is disposable. Document that `docker compose down -v` may be needed. Production uses Render-managed Postgres (handled by Render). |
| **sentry-sdk 2.x init changes** — some integration arguments changed | The `sentry_sdk.init()` call in production.py needs review. Most integrations are auto-detected in 2.x. |

## Migration Plan

1. **Local development first** — upgrade requirements, fix Django code, verify locally
2. **Docker rebuild** — test new Dockerfile and docker-compose.yml locally
3. **Render deployment** — push to Render, verify production works
4. **Cleanup** — remove old Dockerfiles, compose files, env vars after confirmation

**Rollback:** Keep the old `Dockerfile.render`, `local.yml`, and requirements files in git. Revert the commit and redeploy if needed. No database migration rollback needed (Django 5.2 migrations are forward-compatible with 3.2 for this codebase).

## Open Questions

1. **Bootstrap 4 → 5**: Should we do a full template audit now, or upgrade and fix visual issues as they're found? (Recommendation: upgrade and fix as found — most templates will work unchanged.)
2. **Papertrail removal**: Confirmed okay to drop? Render's log viewer covers the same use case.
3. **Docs container**: The `compose/local/docs/` Sphinx container — keep or drop? (Recommendation: drop — can run Sphinx locally if needed.)
