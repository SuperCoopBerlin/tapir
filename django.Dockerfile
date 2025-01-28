FROM python:3.13
ENV PYTHONUNBUFFERED=1
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
    && pip install poetry==1.8.4  \
    && poetry install  \
    && poetry run python manage.py compilemessages
