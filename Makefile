# Fabric Foundry Integration Accelerator — developer commands.
# Python commands always run inside the activated uv virtual environment (.venv).

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

PYTHON_VERSION := 3.14
VENV := .venv
ACTIVATE := source $(VENV)/bin/activate
FRONTEND := frontend

define pending
	@echo "'$@' becomes available in Phase $(1). See phase plan in README.md." >&2; exit 2
endef

.PHONY: help setup setup-backend setup-frontend format lint typecheck test test-cov \
	security sbom privacy-scan sources schemas diagrams education-check fixtures build validate clean data data-check recovery-demo \
	run-api run-mcp run-frontend run demo-check demo-prep demo demo-live demo-hybrid demo-offline

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

# ---------------------------------------------------------------- setup
$(VENV)/bin/activate:
	uv venv --python $(PYTHON_VERSION) $(VENV)

setup: setup-backend setup-frontend ## Install backend and frontend dependencies from lockfiles

setup-backend: $(VENV)/bin/activate ## Create/activate .venv and install locked Python dependencies
	$(ACTIVATE) && uv sync --frozen

setup-frontend: ## Clean-install locked frontend dependencies
	cd $(FRONTEND) && npm ci

# ---------------------------------------------------------------- quality
format: ## Format Python and frontend code
	$(ACTIVATE) && ruff format src tests && ruff check --fix src tests
	cd $(FRONTEND) && npm run format

lint: ## Lint Python and frontend code
	$(ACTIVATE) && ruff check src tests && ruff format --check src tests
	cd $(FRONTEND) && npm run format:check && npm run lint

typecheck: ## Pyright strict + TypeScript strict
	$(ACTIVATE) && pyright
	cd $(FRONTEND) && npm run typecheck

test: ## Run backend and frontend tests
	$(ACTIVATE) && pytest
	cd $(FRONTEND) && npm test

test-cov: ## Run tests with coverage gates (>= 85%)
	$(ACTIVATE) && pytest --cov --cov-report=term-missing
	cd $(FRONTEND) && npm run test:coverage

privacy-scan: ## Scan for customer identifiers, GUIDs, secrets and e-mail addresses
	$(ACTIVATE) && ffia privacy scan

sources: ## Re-render docs/research/source-validation.md from sources.yaml
	$(ACTIVATE) && ffia sources render

schemas: ## Re-export JSON Schemas, OpenAPI and the frontend API types
	$(ACTIVATE) && ffia schemas export

diagrams: ## Render draw.io files and the generated diagram blocks in docs/architecture
	$(ACTIVATE) && ffia diagrams render

education-check: ## Validate lessons, labs, the architecture map and the completeness gate
	$(ACTIVATE) && ffia education check

fixtures: ## Re-export frontend test fixtures from the real API (after model or content changes)
	$(ACTIVATE) && python -m tests.contract.export_frontend_fixtures

data: ## Build Bronze/Silver/Gold for every profile and validate against expected baselines
	$(ACTIVATE) && ffia data build

data-check: ## Verify committed synthetic CSVs are byte-identical to the generator
	$(ACTIVATE) && ffia data generate --check

recovery-demo: ## Run the Open Mirroring snapshot + incremental + restore drill (SIMULATED)
	$(ACTIVATE) && ffia recovery run

security: privacy-scan ## Dependency vulnerability audit (fails on HIGH/CRITICAL) + privacy scan
	$(ACTIVATE) && uv export --quiet --frozen --all-groups --no-emit-project --no-hashes -o /tmp/ffia-requirements-audit.txt \
		&& pip-audit -r /tmp/ffia-requirements-audit.txt --no-deps --disable-pip --progress-spinner off
	cd $(FRONTEND) && npm audit --audit-level=high

sbom: ## Generate CycloneDX SBOMs for Python and frontend into sbom/
	mkdir -p sbom
	$(ACTIVATE) && cyclonedx-py environment --pyproject pyproject.toml --of JSON -o sbom/python.cdx.json $(VENV)/bin/python
	cd $(FRONTEND) && npm sbom --sbom-format cyclonedx --omit dev > ../sbom/frontend.cdx.json

build: ## Build Python distribution and frontend bundle
	$(ACTIVATE) && uv build
	cd $(FRONTEND) && npm run build

validate: lint typecheck test-cov data-check privacy-scan build security ## Full local validation (CI equivalent)
	$(ACTIVATE) && ffia sources check && ffia schemas check && ffia education check && ffia diagrams check && ffia mcp check && ffia notebooks check && ffia skills check && ffia demo offline >/dev/null && echo "offline demo: PASSED"
	@echo "validate: all checks passed"

clean: ## Remove build, cache and coverage artifacts (keeps .venv and node_modules)
	rm -rf dist build sbom .pytest_cache .ruff_cache .coverage coverage.xml htmlcov
	rm -rf $(FRONTEND)/dist $(FRONTEND)/coverage
	find . -name __pycache__ -type d -prune -not -path './.venv/*' -exec rm -rf {} +

# ---------------------------------------------------------------- run (later phases)
run-api: ## Run the FastAPI control plane on http://127.0.0.1:8000 (docs at /docs)
	$(ACTIVATE) && ffia serve api

run-mcp: ## Run the local FastMCP educational server (stdio)
	$(ACTIVATE) && ffia serve mcp

run-frontend: ## Run the frontend dev server
	cd $(FRONTEND) && npm run dev

run: ## Run the API and the frontend together (agents start the stdio MCP server from .mcp.json)
	@trap 'kill 0' INT TERM EXIT; \
	($(ACTIVATE) && ffia serve api) & \
	(cd $(FRONTEND) && npm run dev) & \
	wait

# ---------------------------------------------------------------- demo (later phases)
demo-check: ## Probe Fabric, Foundry, MCP, local dataset, API and frontend; recommend a mode
	$(ACTIVATE) && ffia demo check

demo: ## Check readiness, then run the offline demo (LIVE and HYBRID demos arrive in Phase 6)
	$(ACTIVATE) && ffia demo check && ffia demo offline

demo-live: ## Run the demo against configured live services (read-only by default)
	$(call pending,6)

demo-hybrid: ## Run the demo with available live services and local fallbacks
	$(call pending,6)

demo-prep: ## Before presenting: clear the dev-server cache and run every offline demo check
	rm -rf $(FRONTEND)/node_modules/.vite
	$(ACTIVATE) && ffia demo check --no-azure-cli && ffia mcp check && ffia notebooks check && ffia skills check && ffia demo offline >/dev/null && echo "demo-prep: ready (offline path verified)"

demo-offline: ## Run the ten-act demo with no cloud access (release gate)
	$(ACTIVATE) && ffia demo offline
