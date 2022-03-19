FROM python:3.10
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app

RUN apt update -y && apt install -y libldap2-dev libsasl2-dev gettext

RUN pip install poetry && poetry install \
	    && poetry run python manage.py compilemessages \
	    && poetry run python manage.py compilescss
