# MCP Apple Obsidian - Makefile
# Comprehensive automation for development, testing, and deployment

.PHONY: help setup install install-dev update clean \
        test test-unit test-integration test-coverage test-ci \
        lint format check fix \
        build publish-test publish \
        docs docs-serve \
        install-local uninstall-local install-claude install-kimi \
        bump-version tag-release release

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PACKAGE_NAME := mcp-apple-obsidian
MODULE_NAME := mcp_apple_obsidian
VERSION := $(shell grep -m1 'version = ' pyproject.toml | cut -d'"' -f2)

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "$(BLUE)MCP Apple Obsidian - Available Targets$(NC)"
	@echo "========================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  make setup          # Set up development environment"
	@echo "  make test           # Run all tests"
	@echo "  make install-local  # Install for local testing"

# =============================================================================
# Setup & Installation
# =============================================================================

setup: ## Set up development environment (install uv, dependencies)
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@which uv > /dev/null || (echo "$(YELLOW)Installing uv...$(NC)" && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "$(GREEN)✓ uv installed$(NC)"
	@uv sync
	@echo "$(GREEN)✓ Dependencies installed$(NC)"
	@echo "$(GREEN)✓ Setup complete!$(NC)"

install: ## Install the package
	@echo "$(BLUE)Installing $(PACKAGE_NAME)...$(NC)"
	@uv pip install -e .
	@echo "$(GREEN)✓ Installed$(NC)"

install-dev: ## Install in development mode with all dev dependencies
	@echo "$(BLUE)Installing in development mode...$(NC)"
	@uv sync --extra dev
	@uv pip install -e ".[dev]"
	@echo "$(GREEN)✓ Development install complete$(NC)"

update: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@uv lock --upgrade
	@uv sync
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

clean: ## Clean build artifacts and caches
	@echo "$(BLUE)Cleaning...$(NC)"
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .pytest_cache/ .coverage htmlcov/
	@rm -rf .mypy_cache/ .ruff_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@uv run pytest tests/ -v --tb=short
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	@uv run pytest tests/test_vault_fs.py tests/test_applescript.py tests/test_uri_handler.py -v

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@uv run pytest tests/test_server_integration.py -v

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@uv run pytest --cov=$(MODULE_NAME) --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated: htmlcov/index.html$(NC)"

test-ci: ## Run tests in CI mode (no color, concise)
	@echo "$(BLUE)Running CI tests...$(NC)"
	@uv run pytest tests/ --tb=line -q --color=no

test-specific: ## Run a specific test (use: make test-specific TEST=test_vault_fs.py::TestFrontmatter)
	@uv run pytest tests/$(TEST) -v

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run all linters
	@echo "$(BLUE)Running linters...$(NC)"
	@uv run ruff check src/ tests/
	@uv run ruff format --check src/ tests/
	@echo "$(GREEN)✓ Linting passed$(NC)"

format: ## Format all code
	@echo "$(BLUE)Formatting code...$(NC)"
	@uv run ruff format src/ tests/
	@echo "$(GREEN)✓ Formatting complete$(NC)"

check: ## Run all checks (lint + test)
	@echo "$(BLUE)Running all checks...$(NC)"
	@make lint
	@make test
	@echo "$(GREEN)✓ All checks passed$(NC)"

fix: ## Fix auto-fixable linting issues
	@echo "$(BLUE)Fixing issues...$(NC)"
	@uv run ruff check --fix src/ tests/
	@uv run ruff format src/ tests/
	@echo "$(GREEN)✓ Issues fixed$(NC)"

# =============================================================================
# Building & Publishing
# =============================================================================

build: clean ## Build package for distribution
	@echo "$(BLUE)Building package...$(NC)"
	@uv build
	@echo "$(GREEN)✓ Built: dist/$(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl$(NC)"
	@echo "$(GREEN)✓ Built: dist/$(PACKAGE_NAME)-$(VERSION).tar.gz$(NC)"

publish-test: build ## Publish to TestPyPI
	@echo "$(YELLOW)Publishing to TestPyPI...$(NC)"
	@uv publish --index testpypi dist/*
	@echo "$(GREEN)✓ Published to TestPyPI$(NC)"

publish: build ## Publish to PyPI (production)
	@echo "$(RED)Publishing to PyPI (production)...$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ $$confirm = "y" ] || exit 1
	@uv publish dist/*
	@echo "$(GREEN)✓ Published to PyPI$(NC)"

# =============================================================================
# MCP Server Installation (for users)
# =============================================================================

install-local: ## Install MCP server locally for testing
	@echo "$(BLUE)Installing MCP server locally...$(NC)"
	@uv pip install -e .
	@echo "$(GREEN)✓ Installed. Add to your MCP config:$(NC)"
	@echo '{
	@echo '  "mcpServers": {'
	@echo '    "apple-obsidian": {'
	@echo '      "command": "uvx",
	@echo '      "args": ["--from", "$(PWD)", "mcp-apple-obsidian"]'
	@echo '    }'
	@echo '  }'
	@echo '}'

uninstall-local: ## Uninstall local MCP server
	@echo "$(BLUE)Uninstalling...$(NC)"
	@uv pip uninstall $(PACKAGE_NAME) -y
	@echo "$(GREEN)✓ Uninstalled$(NC)"

install-claude: ## Configure for Claude Desktop (macOS)
	@echo "$(BLUE)Configuring for Claude Desktop...$(NC)"
	@mkdir -p ~/Library/Application\ Support/Claude
	@echo '{
	@echo '  "mcpServers": {'
	@echo '    "apple-obsidian": {'
	@echo '      "command": "uvx",'
	@echo '      "args": ["--from", "$(PWD)", "mcp-apple-obsidian"]'
	@echo '    }'
	@echo '  }'
	@echo '}' > ~/Library/Application\ Support/Claude/claude_desktop_config.json
	@echo "$(GREEN)✓ Configured for Claude Desktop$(NC)"
	@echo "$(YELLOW)Restart Claude Desktop to apply changes$(NC)"

install-kimi: ## Configure for Kimi CLI (macOS/Linux)
	@echo "$(BLUE)Configuring for Kimi CLI...$(NC)"
	@mkdir -p ~/.kimi
	@echo '{
	@echo '  "mcpServers": {'
	@echo '    "apple-obsidian": {'
	@echo '      "command": "uvx",'
	@echo '      "args": ["--from", "$(PWD)", "mcp-apple-obsidian"]'
	@echo '    }'
	@echo '  }'
	@echo '}' > ~/.kimi/mcp.json
	@echo "$(GREEN)✓ Configured for Kimi CLI$(NC)"

# =============================================================================
# Documentation
# =============================================================================

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(GREEN)✓ Documentation:$(NC)"
	@echo "  README.md          - Main documentation"
	@echo "  API.md             - API reference"
	@echo "  AGENTS.md          - Development guide"
	@echo "  TESTING.md         - Testing documentation"

docs-serve: ## Serve documentation locally (if mkdocs available)
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs serve; \
	else \
		echo "$(YELLOW)mkdocs not installed. Install with: uv pip install mkdocs$(NC)"; \
	fi

# =============================================================================
# Release Management
# =============================================================================

bump-version: ## Bump version (use: make bump-version VERSION=0.2.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)Error: VERSION not set. Use: make bump-version VERSION=0.2.0$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Bumping version to $(VERSION)...$(NC)"
	@sed -i.bak 's/version = "[^"]*"/version = "$(VERSION)"/' pyproject.toml && rm pyproject.toml.bak
	@sed -i.bak 's/__version__ = "[^"]*"/__version__ = "$(VERSION)"/' src/$(MODULE_NAME)/__init__.py && rm src/$(MODULE_NAME)/__init__.py.bak
	@echo "$(GREEN)✓ Version bumped to $(VERSION)$(NC)"
	@echo "$(YELLOW)Don't forget to update CHANGELOG.md$(NC)"

tag-release: ## Create git tag for release
	@echo "$(BLUE)Creating tag v$(VERSION)...$(NC)"
	@git add -A
	@git commit -m "Release v$(VERSION)" || true
	@git tag -a "v$(VERSION)" -m "Release v$(VERSION)"
	@echo "$(GREEN)✓ Tagged v$(VERSION)$(NC)"
	@echo "$(YELLOW)Push with: git push origin v$(VERSION)$(NC)"

release: ## Full release workflow (build + tag)
	@make check
	@make build
	@make tag-release
	@echo "$(GREEN)✓ Release v$(VERSION) ready!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Push tag: git push origin v$(VERSION)"
	@echo "  2. Create GitHub release"
	@echo "  3. Publish to PyPI: make publish"

# =============================================================================
# Development Utilities
# =============================================================================

run: ## Run the MCP server locally
	@uv run mcp-apple-obsidian

inspector: ## Run MCP Inspector for testing
	@echo "$(BLUE)Starting MCP Inspector...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@npx @modelcontextprotocol/inspector uv run mcp-apple-obsidian

debug: ## Run with debug logging
	@OBSIDIAN_LOG_LEVEL=debug uv run mcp-apple-obsidian

shell: ## Open Python shell with package loaded
	@uv run python -c "from mcp_apple_obsidian import *; print('Package loaded. Available: vault_fs, applescript, uri_handler, server')" -i

# =============================================================================
# Maintenance
# =============================================================================

update-deps: ## Update dependencies and lock file
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@uv lock --upgrade
	@uv sync
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

audit: ## Run security audit
	@echo "$(BLUE)Running security audit...$(NC)"
	@uv pip audit || echo "$(YELLOW)pip audit not available$(NC)"
	@echo "$(GREEN)✓ Audit complete$(NC)"

verify: ## Verify installation
	@echo "$(BLUE)Verifying installation...$(NC)"
	@uv run python -c "from mcp_apple_obsidian import mcp, main; print('✓ Package imports successfully')"
	@uv run python -c "import mcp_apple_obsidian; print(f'✓ Version: {mcp_apple_obsidian.__version__}')"
	@which mcp-apple-obsidian > /dev/null && echo "✓ CLI available" || echo "✗ CLI not available"
	@echo "$(GREEN)✓ Verification complete$(NC)"

# =============================================================================
# Docker (optional)
# =============================================================================

docker-build: ## Build Docker image (if Dockerfile exists)
	@if [ -f Dockerfile ]; then \
		docker build -t $(PACKAGE_NAME):$(VERSION) .; \
	else \
		echo "$(YELLOW)No Dockerfile found$(NC)"; \
	fi

docker-run: ## Run in Docker container
	@docker run --rm -it $(PACKAGE_NAME):$(VERSION)

# =============================================================================
# Aliases
# =============================================================================

dev: install-dev ## Alias for install-dev
t: test ## Alias for test
c: check ## Alias for check
fmt: format ## Alias for format
