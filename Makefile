.PHONY: clean
clean: clean-build clean-pyc clean-test clean-docs

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr deployments/build/
	rm -fr deployments/Dockerfiles/open_aea/packages
	rm -fr pip-wheel-metadata
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +
	find . -name '*.svn' -exec rm -fr {} +
	find . -name '*.db' -exec rm -fr {} +
	rm -fr .idea .history
	rm -fr venv

.PHONY: clean-docs
clean-docs:
	rm -fr site/

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test:
	rm -fr .tox/
	rm -f .coverage
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;
	rm -fr coverage.xml
	rm -fr htmlcov/
	rm -fr .hypothesis
	rm -fr .pytest_cache
	rm -fr .mypy_cache/
	find . -name 'log.txt' -exec rm -fr {} +
	find . -name 'log.*.txt' -exec rm -fr {} +

.PHONY: tests
tests:
	poetry run pytest tests -vv --reruns 3 --reruns-delay 10

.PHONY: fmt
fmt:
	poetry run ruff format tests derive_client examples scripts
	poetry run ruff check tests derive_client examples scripts --fix

.PHONY: lint
lint:
	poetry run ruff check tests derive_client examples scripts


test-docs:
	echo making docs

release:
	$(eval current_version := $(shell poetry run tbump current-version))
	@echo "Current version is $(current_version)"
	$(eval new_version := $(shell python -c "import semver; print(semver.bump_patch('$(current_version)'))"))
	@echo "New version is $(new_version)"
	poetry run tbump $(new_version)

.PHONY: generate-models
generate-models:
	curl https://docs.derive.xyz/openapi/rest-api.json | jq > openapi-spec.json
	poetry run python scripts/patch_spec.py openapi-spec.json
	poetry run python scripts/generate-models.py
	poetry run ruff format derive_client/data_types/generated_models.py
	poetry run ruff check --fix derive_client/data_types/generated_models.py

.PHONY: generate-rest-api
generate-rest-api:
	python scripts/generate-rest-api.py
	poetry run ruff format derive_client/_clients/rest/
	poetry run ruff check --fix derive_client/_clients/rest/

.PHONY: generate-rest-async-http
generate-rest-async-http:
	python scripts/generate-rest-async-http.py
	poetry run ruff format tests/test_clients/test_rest/test_async_http
	poetry run ruff check --fix tests/test_clients/test_rest/test_async_http

.PHONY: generate-sync-bridge-client
generate-sync-bridge-client:
	python scripts/generate-sync-bridge-client.py
	poetry run ruff format derive_client/_bridge/client.py
	poetry run ruff check --fix derive_client/_bridge/client.py


codegen-all: generate-models generate-rest-api generate-rest-async-http generate-sync-bridge-client fmt lint

typecheck:
	poetry run pyright derive_client

check_diff:
	@git diff --exit-code

all: codegen-all fmt lint typecheck tests
