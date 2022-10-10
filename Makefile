lint:
	poetry run black .

test-lint:
	poetry run black --check .

test:
	poetry run pytest --cov-report xml:coverage.xml
