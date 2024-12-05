#!/bin/sh

docker compose run --rm web poetry run python ./manage.py spectacular --file schema.yml