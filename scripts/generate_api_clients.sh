#!/bin/sh

docker compose exec vite npx openapi-generator-cli generate -i schema.yml -g typescript-fetch -o ./src/api-client