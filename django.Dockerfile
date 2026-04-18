# syntax=docker/dockerfile:1
ARG USER_UID
ARG USER_GID


FROM python:3.13 AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 
ENV POETRY_VERSION=2.3.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_NO_INTERACTION=1 

ENV PATH="$POETRY_HOME/bin:$PATH"


RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential curl \
    libpq-dev \
    gettext \
    libldap2-dev  libsasl2-dev \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
    

RUN curl -sS https://install.python-poetry.org | POETRY_HOME=$POETRY_HOME python3 - 

RUN apt-get clean && rm -rf /var/lib/apt/lists/*


FROM base as builder

WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN poetry install --only main --no-root


FROM base as dev
ARG USER_UID
ARG USER_GID
RUN groupadd -g $USER_GID appuser && \
    useradd -u $USER_UID -g $USER_GID -m appuser

WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root

ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=appuser:appuser Makefile manage.py ./
COPY --chown=appuser:appuser tapir ./tapir
RUN chown -R appuser:appuser /app


RUN poetry run python manage.py compilemessages
USER appuser



FROM python:3.13-slim AS prod
ARG ARG_VERSION
ARG USER_UID
ARG USER_GID
ENV TAPIR_VERSION=${ARG_VERSION}
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq-dev gettext libldap2-dev libsasl2-dev  \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid $USER_GID appuser && \
    useradd --uid $USER_UID --gid $USER_GID -m appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser manage.py ./
COPY --chown=appuser:appuser tapir ./tapir

RUN python manage.py compilemessages

USER appuser
