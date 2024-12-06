#!/bin/sh

docker compose cp ./dump.tar db:dump.tar
docker compose exec db pg_restore -c -U tapir -d tapir dump.tar