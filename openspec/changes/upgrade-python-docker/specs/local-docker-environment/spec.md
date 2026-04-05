## ADDED Requirements

### Requirement: Local Docker Compose provides a complete development stack
The system SHALL provide a `docker-compose.yml` file at the project root that starts all services needed for local development and self-hosted deployment with a single `docker compose up` command.

#### Scenario: Full stack starts with one command
- **WHEN** a user runs `docker compose up` from the project root
- **THEN** all services (Django, PostgreSQL, Redis, Mailpit, Adminer) start and are accessible at their documented ports

### Requirement: Django service runs Python 3.13 with Django 5.2
The Django container SHALL use Python 3.13-slim-bookworm as its base image and run Django 5.2 with the local settings module.

#### Scenario: Django container starts successfully
- **WHEN** the Django service starts
- **THEN** it runs on port 8000, connects to PostgreSQL, Redis, and serves the application with DEBUG=True

### Requirement: PostgreSQL 17 service with persistent data
The system SHALL include a PostgreSQL 17 container with a named Docker volume for data persistence across container restarts.

#### Scenario: Database data persists across restarts
- **WHEN** `docker compose down` and `docker compose up` are run sequentially
- **THEN** all database data remains intact

### Requirement: Redis 7 service for caching and sessions
The system SHALL include a Redis 7 container accessible by the Django service for caching and session storage.

#### Scenario: Django uses Redis for caching
- **WHEN** the Django service starts
- **THEN** it connects to the Redis service and uses it as the cache backend

### Requirement: Mailpit service for email testing
The system SHALL include a Mailpit container that captures all outgoing emails and provides a web UI on port 8025 for viewing them.

#### Scenario: Emails are captured and viewable
- **WHEN** Django sends an email (e.g., account verification)
- **THEN** the email appears in the Mailpit web UI at port 8025

### Requirement: Adminer service for database administration
The system SHALL include an Adminer container on port 8080 pre-configured to connect to the PostgreSQL service.

#### Scenario: Database admin UI is accessible
- **WHEN** a user navigates to port 8080 in a browser
- **THEN** Adminer loads with the PostgreSQL connection pre-filled

### Requirement: Environment configuration via .env files
The system SHALL use `.envs/.local/.django` and `.envs/.local/.postgres` files for environment variable configuration, matching the existing convention.

#### Scenario: Environment variables are loaded
- **WHEN** `docker compose up` runs
- **THEN** Django receives DATABASE_URL, SECRET_KEY, and all required settings from the .env files
