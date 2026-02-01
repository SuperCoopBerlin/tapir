lint:
	black .

check-formatting:
	black --check .

test:
	pytest --cov-report xml:coverage.xml --cov=tapir --cov-config=pyproject.toml

check-translations:
    ls -la /app
	cp tapir/translations/locale/de/LC_MESSAGES/django.po tapir/translations/locale/de/LC_MESSAGES/django-old.po
	cd tapir && python ../manage.py makemessages --no-wrap -l de
	git diff --ignore-matching-lines=POT-Creation-Date --exit-code --no-index tapir/translations/locale/de/LC_MESSAGES/django.po tapir/translations/locale/de/LC_MESSAGES/django-old.po
	rm tapir/translations/locale/de/LC_MESSAGES/django-old.po

check-migrations:
	python manage.py makemigrations --check
