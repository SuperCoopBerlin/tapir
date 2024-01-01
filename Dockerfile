# ---------------------------------------------------------------------------------------
# BASE
# ---------------------------------------------------------------------------------------
FROM python:3.11-buster as base
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

ENV PATH="/.venv/bin:$PATH"
ENV POETRY_VERSION=1.7.0

# ---------------------------------------------------------------------------------------
# TESTING
# ---------------------------------------------------------------------------------------
FROM base as testing

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./
# weasyprint: libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
# psycopg2: libpq5
RUN apt update -y && apt install -y libldap2-dev libsasl2-dev libpq5 gettext libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
RUN poetry install --with dev

WORKDIR /app
COPY . .

RUN python manage.py compilemessages --ignore \".venv\"
RUN python manage.py runserver_plus 0.0.0.0:80

# ---------------------------------------------------------------------------------------
# BUILD
# ---------------------------------------------------------------------------------------
FROM base as builder

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

RUN apt update -y && apt install -y libldap2-dev libsasl2-dev gettext
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR


# ---------------------------------------------------------------------------------------
# RUN/PRODUCTION
# ---------------------------------------------------------------------------------------
# The runtime image, used to just run the code provided its virtual environment
FROM base as runtime

# weasyprint: libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
# psycopg2: libpq5
RUN apt update -y && apt upgrade -y && apt install -y libpq5 gettext libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 &&  \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

COPY --from=builder /.venv /.venv

WORKDIR /app
COPY . .

RUN python manage.py compilemessages --ignore \".venv\"
RUN python manage.py runserver 0.0.0.0:80