ARG PYTHON_VERSION=3.13-slim-bookworm

FROM python:${PYTHON_VERSION} AS python-build-stage

ARG BUILD_ENVIRONMENT=local

RUN apt-get update && apt-get install --no-install-recommends -y \
  build-essential \
  libpq-dev

COPY ./requirements .

RUN pip wheel --wheel-dir /usr/src/app/wheels \
  -r ${BUILD_ENVIRONMENT}.txt


FROM python:${PYTHON_VERSION} AS python-run-stage

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN addgroup --system django \
    && adduser --system --ingroup django --home /home/django django

RUN apt-get update && apt-get install --no-install-recommends -y \
  libpq-dev \
  gettext \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY --from=python-build-stage /usr/src/app/wheels /wheels/

RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/

# Entrypoint: wait for postgres, then exec
RUN printf '#!/bin/bash\n\
set -o errexit\n\
set -o pipefail\n\
set -o nounset\n\
\n\
postgres_ready() {\n\
python << PYEOF\n\
import sys, os\n\
# Support both DATABASE_URL (Render) and individual POSTGRES_* vars (Docker Compose)\n\
database_url = os.environ.get("DATABASE_URL", "")\n\
if database_url:\n\
    from urllib.parse import urlparse\n\
    parsed = urlparse(database_url)\n\
    db = {\n\
        "NAME": parsed.path.lstrip("/"),\n\
        "USER": parsed.username or "",\n\
        "PASSWORD": parsed.password or "",\n\
        "HOST": parsed.hostname or "",\n\
        "PORT": str(parsed.port or 5432),\n\
    }\n\
else:\n\
    db = {\n\
        "NAME": os.environ.get("POSTGRES_DB", ""),\n\
        "USER": os.environ.get("POSTGRES_USER", "postgres"),\n\
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),\n\
        "HOST": os.environ.get("POSTGRES_HOST", ""),\n\
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),\n\
    }\n\
if not db.get("HOST"):\n\
    sys.exit(0)\n\
import psycopg2\n\
try:\n\
    psycopg2.connect(\n\
        dbname=db["NAME"],\n\
        user=db["USER"],\n\
        password=db["PASSWORD"],\n\
        host=db["HOST"],\n\
        port=db["PORT"],\n\
    )\n\
except psycopg2.OperationalError:\n\
    sys.exit(-1)\n\
sys.exit(0)\n\
PYEOF\n\
}\n\
until postgres_ready; do\n\
  echo "Waiting for PostgreSQL..."\n\
  sleep 1\n\
done\n\
echo "PostgreSQL is available"\n\
exec "$@"\n' > /entrypoint \
  && chmod +x /entrypoint

# Start script: migrate + collectstatic + gunicorn
# Render sets PORT env var; default to 5000 for local
RUN printf '#!/bin/bash\n\
set -o errexit\n\
set -o pipefail\n\
set -o nounset\n\
\n\
python /app/manage.py migrate --noinput\n\
python /app/manage.py collectstatic --noinput\n\
/usr/local/bin/gunicorn config.wsgi --bind 0.0.0.0:${PORT:-5000} --chdir=/app\n' > /start \
  && chmod +x /start

COPY --chown=django:django . ${APP_HOME}

RUN chown django:django ${APP_HOME}

USER django

ENTRYPOINT ["/entrypoint"]
CMD ["/start"]
