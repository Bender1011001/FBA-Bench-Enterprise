#!/usr/bin/env bash
# FBA-Bench Installation Script for Linux/macOS
# Installs dependencies for this repository using Poetry (backend only; legacy frontend removed).

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Requirements checks
if ! command -v python3 >/dev/null 2>&1; then
  print_error "Python 3 is not installed. Install Python >=3.9."
  exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
print_status "Detected Python ${PYTHON_VERSION}"

# Install Poetry if missing; prefer python -m poetry to avoid PATH issues
ensure_poetry() {
  if python3 -m poetry --version >/dev/null 2>&1; then
    return 0
  fi
  print_status "Installing Poetry..."
  if command -v pipx >/dev/null 2>&1; then
    pipx install poetry || true
  fi
  if ! python3 -m poetry --version >/dev/null 2>&1; then
    python3 -m pip install --user --upgrade pip
    python3 -m pip install --user poetry
  fi
  if ! python3 -m poetry --version >/dev/null 2>&1; then
    print_error "Failed to install Poetry."
    exit 1
  fi
}

print_status "Ensuring Poetry is available..."
ensure_poetry

print_status "Installing backend dependencies with Poetry..."
python3 -m poetry install --with dev --no-interaction --no-ansi

print_success "Installation completed."

echo
print_status "Next steps:"
echo " - Run the API locally:"
echo "     python3 -m poetry run uvicorn fba_bench_api.main:create_app --factory --host 0.0.0.0 --port 8000 --reload"
echo " - Optional: Start ClearML Server for experiment tracking:"
echo "     docker compose -f docker-compose.clearml.yml up -d"
