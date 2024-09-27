lint:
	poetry run black .

check-formatting:
	poetry run black --check .

test:
	poetry run pytest --cov-report xml --cov=tapir

check-translations:
	cp tapir/translations/locale/de/LC_MESSAGES/django.po tapir/translations/locale/de/LC_MESSAGES/django-old.po
	cd tapir && poetry run python ../manage.py makemessages --no-wrap -l de
	git diff --ignore-matching-lines=POT-Creation-Date --exit-code --no-index tapir/translations/locale/de/LC_MESSAGES/django.po tapir/translations/locale/de/LC_MESSAGES/django-old.po
	rm tapir/translations/locale/de/LC_MESSAGES/django-old.po

check-migrations:
	poetry run python manage.py makemigrations --check