FROM python:3.12
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app

RUN apt update -y  \
    && apt --no-install-recommends install -y libldap2-dev libsasl2-dev gettext postgresql-client-common postgresql-client  \
    && rm -rf /var/lib/apt/lists/*  \
    && pip install poetry  \
    && poetry install  \
    && poetry run python manage.py compilemessages
