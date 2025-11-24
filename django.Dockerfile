# syntax=docker/dockerfile:1

FROM python:3.13-slim AS build

ENV POETRY_VERSION=2.2.1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN pip install "poetry==$POETRY_VERSION"
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential \
    # psycopg2 dependencies
    libpq-dev \
    # Translations dependencies
    gettext \
    # LDAP dependencies
    libldap2-dev  libsasl2-dev  \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*
WORKDIR $PYSETUP_PATH

COPY poetry.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-root

COPY . .

FROM python:3.13 AS runtime

ENV VENV_PATH="/opt/pysetup/.venv" \
    PATH="/opt/pysetup/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    # psycopg2 dependencies
    libpq-dev \
    # Translations dependencies
    gettext \
    # LDAP dependencies
    libldap2-dev libsasl2-dev  \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/bash appuser

WORKDIR /app

COPY --from=build --chown=appuser:appgroup /opt/pysetup/.venv /opt/pysetup/.venv
COPY --from=build --chown=appuser:appgroup /opt/pysetup/ ./
COPY --chown=appuser:appgroup . .
USER appuser