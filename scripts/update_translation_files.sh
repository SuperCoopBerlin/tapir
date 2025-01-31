#!/bin/sh

# translations from Python
docker compose run --rm -w /app/tapir web poetry run python ../manage.py makemessages --no-wrap -l de

# translations from Javascript
docker compose run --rm vite npm run build
docker compose run --rm -w /app web poetry run python manage.py makemessages --no-wrap -l de -d djangojs