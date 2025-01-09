# Crypto Anomaly Detection Engine (CADE)
#
# Multi-stage Dockerfile for building and running the CADE system
#
# Author: CADE
# Team License: Proprietary

# Stage 1: Base Python image
FROM python:3.11-slim as python-base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.4.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Stage 2: Builder image
FROM python-base as builder
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential \
        git

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy project dependency files
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./
COPY ./src ./src

# Install runtime dependencies
RUN poetry install --only main

# Stage 3: Development image
FROM python-base as development
ENV FLASK_ENV=development \
    FLASK_DEBUG=1

WORKDIR $PYSETUP_PATH

# Copy dependencies from builder
COPY --from=builder $POETRY_HOME $POETRY_HOME
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

# Copy development configs and scripts
COPY config/development.yml /app/config/
COPY scripts/dev-entrypoint.sh /app/scripts/

# Install development dependencies
RUN poetry install

# Set up development entrypoint
ENTRYPOINT ["/app/scripts/dev-entrypoint.sh"]

# Stage 4: Production image
FROM python-base as production
ENV FLASK_ENV=production \
    FLASK_DEBUG=0

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder $VENV_PATH $VENV_PATH
COPY --from=builder $PYSETUP_PATH/src /app/src

# Copy production configs and scripts
COPY config/production.yml /app/config/
COPY scripts/prod-entrypoint.sh /app/scripts/

# Create non-root user
RUN useradd -m -u 1000 cade && \
    chown -R cade:cade /app

USER cade

# Set up production entrypoint
ENTRYPOINT ["/app/scripts/prod-entrypoint.sh"]