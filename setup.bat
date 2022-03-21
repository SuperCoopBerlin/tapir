docker-compose exec web poetry run python manage.py migrate
docker-compose exec web poetry run python manage.py loaddata admin_account
docker-compose exec web poetry run python manage.py populate --reset_all