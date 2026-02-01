# syntax=docker/dockerfile:1

FROM python:3.13-slim AS build
ARG DEV=false
ENV POETRY_VERSION=2.2.1 \
    PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"


RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential curl \
    # psycopg2 dependencies
    libpq-dev \
    # Translations dependencies
    gettext \
    # LDAP dependencies
    libldap2-dev  libsasl2-dev  \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=$POETRY_HOME python3 - && \
    ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry

WORKDIR $PYSETUP_PATH

COPY poetry.lock pyproject.toml ./

RUN if [ "$DEV" = "true" ]; then \
      poetry install --with dev --no-root; \
    else \
      poetry install --without dev --no-root; \
    fi


FROM python:3.13-slim AS runtime
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG USERNAME=nonroot

ENV VENV_PATH="/opt/pysetup/.venv" \
    PATH="/opt/pysetup/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq-dev gettext libldap2-dev libsasl2-dev  \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    make git \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid $USER_GID nonroot && \
    useradd --uid $USER_UID --gid $USER_GID -m nonroot && \
    mkdir -p /app

USER $USERNAME

WORKDIR /app

COPY --from=build --chown=$USERNAME:$USERNAME /opt/pysetup/.venv /opt/pysetup/.venv
COPY --from=build --chown=$USERNAME:$USERNAME /opt/pysetup/ ./
COPY --chown=$USERNAME:$USERNAME . .

RUN python manage.py compilemessages


