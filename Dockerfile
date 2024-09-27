FROM python:3.12
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app

RUN apt update -y  \
    && apt --no-install-recommends install -y  \
        gettext  \
        libldap2-dev  \
        libsasl2-dev  \
        postgresql-client  \
        postgresql-client-common \
    && rm -rf /var/lib/apt/lists/*  \
    && pip install poetry  \
    && poetry install  \
    && poetry run python manage.py compilemessages
