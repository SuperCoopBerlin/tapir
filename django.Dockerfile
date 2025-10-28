FROM python:3.13
ENV PYTHONUNBUFFERED=1

RUN apt-get update -y  \
    && apt-get --no-install-recommends install -y  \
        gettext  \
        libldap2-dev  \
        libsasl2-dev  \
        postgresql-client  \
        postgresql-client-common  \
        python3-poetry  \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m developer
WORKDIR /app
COPY --chown=developer:developer . /app

USER developer

RUN poetry install  \
    && poetry run python manage.py compilemessages
