# Show available recipes
default:
    @just --list --unsorted

# Run all available recipes
all: lint typecheck test coverage build docs-build

# Sync development dependencies (may update uv.lock if pyproject.toml changed)
sync *ARGS:
    uv sync {{ARGS}} --group dev

# Lint and format source code
lint:
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/

# Lint bash scripts
lint-bash:
    shfmt -i 4 -ci -w scripts/bubble-agent.sh
    shellcheck scripts/bubble-agent.sh

# Run static type checks with Astral ty
typecheck:
    uv run ty check src/

# Run tests
test *ARGS:
    uv run pytest -v {{ARGS}} tests/

# Run tests with coverage report
coverage:
    uv run pytest --cov=bubble_agent --cov-report=term-missing tests/

# Build distribution packages
build:
    uv build

# Install bubble-agent as a tool
install:
    #!/usr/bin/env bash
    set -euo pipefail
    uv tool install .

# Uninstall bubble-agent
uninstall:
    uv tool uninstall bubble-agent

# Serve documentation locally
docs-serve:
    uv run zensical serve

# Build documentation
docs-build:
    uv run zensical build

# Remove build artifacts
clean:
    rm -rf dist/ site/ .cache/ .ruff_cache/ .pytest_cache/ htmlcov/ .coverage
    find src/ tests/ -type f -name "*.pyc" -delete
    find src/ tests/ -type d -name "__pycache__" -delete
