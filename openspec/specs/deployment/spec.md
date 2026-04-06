## ADDED Requirements

### Requirement: Single Dockerfile for local and production
The system SHALL use a single multi-stage Dockerfile (`Dockerfile`) that works for both local development and Render deployment. The Dockerfile SHALL use Python 3.13-slim-bookworm as its base image.

#### Scenario: Dockerfile builds successfully
- **WHEN** `docker build -t budgetbuddy .` is run from the project root
- **THEN** the image builds without errors and runs the Django application

#### Scenario: Render deploys from the same Dockerfile
- **WHEN** Render builds the application using the Dockerfile
- **THEN** the application starts and serves requests on the configured port

### Requirement: render.yaml references the new Dockerfile
The `render.yaml` SHALL point at the new `Dockerfile` (not `Dockerfile.render`). The `RAPID_API_KEY` environment variable SHALL be removed from the envVars list.

#### Scenario: Render deployment configuration is valid
- **WHEN** Render reads `render.yaml`
- **THEN** it finds a valid `dockerfilePath: Dockerfile` and all required environment variables

## MODIFIED Requirements

### Requirement: Production Dockerfile uses standard multi-stage build
The production Dockerfile SHALL be replaced from the buildpack-based `Dockerfile.render` with a standard multi-stage Dockerfile. It SHALL install dependencies via pip wheels, create a non-root user, and run Django via gunicorn.

#### Scenario: Production container starts with gunicorn
- **WHEN** the production container starts
- **THEN** it runs gunicorn as the web server with the configured `WEB_CONCURRENCY`

## REMOVED Requirements

### Requirement: Buildpack-based Dockerfile.render
**Reason**: Replaced by standard multi-stage Dockerfile that works everywhere
**Migration**: Remove `Dockerfile.render` and update `render.yaml` to point at `Dockerfile`

### Requirement: Papertrail log forwarding
**Reason**: Render provides built-in log viewing; Papertrail is redundant
**Migration**: Remove `PAPERTRAIL_API_TOKEN` environment variable and any Papertrail configuration

### Requirement: RapidAPI stock price fetching
**Reason**: Replaced by yfinance library (see yfinance-stock-prices spec)
**Migration**: Remove `RAPID_API_KEY` from render.yaml and all deployment environments

### Requirement: Traefik reverse proxy Docker setup
**Reason**: Not used in local development or Render deployment; single-app setup does not need a reverse proxy
**Migration**: Remove `compose/production/traefik/` directory

### Requirement: Sphinx docs Docker container
**Reason**: Rarely used; Sphinx can be run locally when needed
**Migration**: Remove `compose/local/docs/` directory and docs service from docker-compose
