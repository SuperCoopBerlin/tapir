FROM python:3.13
ENV PYTHONUNBUFFERED=1
ARG ARG_VERSION
ARG POETRY_INSTALL_DEV=true
ENV TAPIR_VERSION=${ARG_VERSION}
WORKDIR /app
COPY . /app

RUN apt-get update -y  \
    && apt-get --no-install-recommends install -y  \
        gettext  \
        libldap2-dev  \
        libsasl2-dev  \
        postgresql-client  \
        postgresql-client-common \
    && rm -rf /var/lib/apt/lists/*  \
    && pip install poetry

RUN if [ "${POETRY_INSTALL_DEV}" = "false" ]; then \
      poetry install --no-interaction --without dev; \
    else \
      poetry install --no-interaction; \
    fi
RUN poetry run python manage.py compilemessages
