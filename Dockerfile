# ---------------------------------------------------------------------------------------
# BUILD
# ---------------------------------------------------------------------------------------
FROM python:3.11-buster as builder
ENV POETRY_VERSION=1.7.0

RUN pip install "poetry==$POETRY_VERSION"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache


COPY pyproject.toml poetry.lock ./

RUN apt update -y && apt install -y libldap2-dev libsasl2-dev gettext  # this is mainly necessary for building python-ldap
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# ---------------------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------------------
# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-buster as runtime
# pangotools: for weasyprint
# libpq5: for psycopg2
RUN apt update -y && apt upgrade -y && apt install -y libpq5 gettext pango1.0-tools && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/.venv \
    PATH="/.venv/bin:$PATH"


COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY . ./
#CMD python manage.py runserver
#CMD python manage.py runserver_plus 0.0.0.0:80
RUN python manage.py compilemessages
#RUN python manage.py runserver_plus 0.0.0.0:80


# Before 1.54GB
# After  313MB