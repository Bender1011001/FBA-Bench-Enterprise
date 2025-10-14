.PHONY: be-migrate be-test lint format-check format-fix type-check test-contracts test-all coverage ci-local pre-commit-install pre-commit-run

# Use Poetry to run all Python tooling by default
POETRY ?= poetry

# -----------------------------------------------------------------------------
# Backend commands (legacy shims)
# -----------------------------------------------------------------------------
be-migrate:
	$(POETRY) run dotenv run alembic upgrade head

be-test:
	$(POETRY) run pytest -q

# -----------------------------------------------------------------------------
# Quality gates (mirror CI)
# -----------------------------------------------------------------------------
lint:
	$(POETRY) run ruff check .

format-check:
	$(POETRY) run ruff format --check .
	$(POETRY) run black --check .

format-fix:
	$(POETRY) run ruff format .
	$(POETRY) run black .

type-check:
	$(POETRY) run mypy src

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
test-contracts:
	$(POETRY) run pytest -q tests/contracts

test-all:
	$(POETRY) run pytest --cov=src --cov-report=xml --cov-fail-under=80

# Timeboxed full test run to avoid local hangs; respects pytest-timeout settings from pyproject
test-all-timeboxed:
	$(POETRY) run pytest --cov=src --cov-report=xml --maxfail=1 -vv -s

coverage: test-all

# -----------------------------------------------------------------------------
# Verification helpers
# -----------------------------------------------------------------------------
verify-golden:
	$(POETRY) run python scripts/verify_golden_masters.py

verify-coverage:
	$(POETRY) run python scripts/verify_coverage_thresholds.py

# -----------------------------------------------------------------------------
# CI parity aggregate
# -----------------------------------------------------------------------------
ci-local:
	$(MAKE) lint
	$(MAKE) format-check
	$(MAKE) type-check
	$(MAKE) test-contracts
	$(MAKE) test-all
	$(MAKE) verify-golden
	$(MAKE) verify-coverage

# -----------------------------------------------------------------------------
# Pre-commit helpers
# -----------------------------------------------------------------------------
pre-commit-install:
	$(POETRY) run pre-commit install --install-hooks

pre-commit-run:
	$(POETRY) run pre-commit run --all-files --show-diff-on-failure

# -----------------------------------------------------------------------------
# Database migrations
# -----------------------------------------------------------------------------
db-migrate:
	$(POETRY) run alembic upgrade head

# -----------------------------------------------------------------------------
# Build targets
# -----------------------------------------------------------------------------
build:
	docker-compose build

frontend-build:
	cd frontend && npm ci && npm run build
	cp -r frontend/dist ./static

# -----------------------------------------------------------------------------
# Deployment
# -----------------------------------------------------------------------------
deploy:
	docker-compose -f docker-compose.prod.yml up -d

deploy-down:
	docker-compose -f docker-compose.prod.yml down

# -----------------------------------------------------------------------------
# Load Testing
# -----------------------------------------------------------------------------
load-test:
	poetry run locust -f locustfile.py --headless -u 10 -r 2 --run-time 30s --host=http://localhost:8000

# -----------------------------------------------------------------------------
# CI enhancements
# -----------------------------------------------------------------------------
ci-docker:
	$(MAKE) build
	docker-compose run api make ci-local

ci-local: lint format-check type-check test-contracts test-all load-test

# -----------------------------------------------------------------------------
# Deployment targets
# -----------------------------------------------------------------------------
VERSION ?= 1.0.0
IMAGE_NAME ?= fba-bench-app
REGISTRY ?= docker.io/$(USER)

deploy-prod:
	docker-compose -f docker-compose.prod.yml up -d --build

rollback:
	docker-compose -f docker-compose.prod.yml down
	@echo "Rollback complete. To restore previous version, pull specific image tag or use git revert."

release: deploy-prod
	git tag -a v$(VERSION) -m "Release v$(VERSION)"
	git push origin v$(VERSION)
	docker build -t $(REGISTRY)/$(IMAGE_NAME):$(VERSION) -f Dockerfile.prod .
	docker push $(REGISTRY)/$(IMAGE_NAME):$(VERSION)
	docker tag $(REGISTRY)/$(IMAGE_NAME):$(VERSION) $(REGISTRY)/$(IMAGE_NAME):latest
	docker push $(REGISTRY)/$(IMAGE_NAME):latest
	@echo "Release v$(VERSION) tagged, pushed, and deployed."

# -----------------------------------------------------------------------------
# Development Startup
# -----------------------------------------------------------------------------
start:
	scripts\\fba-start.bat
