#!/bin/sh

docker compose down
docker compose up -d --remove-orphans
docker compose exec web poetry run python manage.py migrate
docker compose exec web poetry run python manage.py generate_test_data --reset_all