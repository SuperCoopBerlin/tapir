lint:
    black .

test-lint:
	black --check .

test:
	pytest --cov-report xml:coverage.xml
