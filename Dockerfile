FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app

RUN apt update -y && apt install -y libldap2-dev libsasl2-dev gettext

RUN pip install poetry && poetry install && poetry run python manage.py compilemessages

# Run collectstatic at startup to possibly copy to a shared volume to be served by nginx
CMD ["sh", "-c", "poetry run ./manage.py collectstatic && poetry run gunicorn -b 0.0.0.0:80 tapir.wsgi:application"]
