lint:
	poetry run black .

test-lint:
	poetry run black --check .

test: test-lint
	poetry run ./manage.py makemigrations --check
	poetry run pytest
