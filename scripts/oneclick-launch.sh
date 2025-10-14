#!/usr/bin/env bash
set -euo pipefail

# Check for Docker
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed or not in PATH. Please install Docker Desktop or Docker Engine."
  exit 1
fi

if ! docker info &> /dev/null 2>&1; then
  echo "Error: Docker daemon is not running. Please start Docker."
  exit 1
fi

# Check for Docker Compose
if ! docker compose version &> /dev/null; then
  echo "Error: Docker Compose is not available. Please ensure Docker Compose v2 is installed."
  exit 1
fi

# Determine repo root (parent of scripts directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse arguments
MODE="test"  # default to --test if no flag
while [[ $# -gt 0 ]]; do
  case $1 in
    --full)
      MODE="full"
      shift
      ;;
    --test)
      MODE="test"
      shift
      ;;
    --help|-h)
      echo "Usage: ./oneclick-launch.sh [--full | --test]"
      echo "  --full: Launch full stack for researchers (detached mode)"
      echo "  --test: Launch test setup for single-user testing (foreground mode)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./oneclick-launch.sh [--full | --test]"
      exit 1
      ;;
  esac
done

# Set compose file and messages based on mode
if [[ "$MODE" == "full" ]]; then
  COMPOSE_FILE="$REPO_ROOT/docker-compose.full.yml"
  echo "==> Launching full stack..."
else
  COMPOSE_FILE="$REPO_ROOT/docker-compose.test.yml"
  echo "==> Launching test setup..."
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE"
  echo "Ensure files are created and you are in the correct repository."
  exit 1
fi

if [[ ! -f "$REPO_ROOT/.env" ]]; then
  echo "Warning: .env not found at $REPO_ROOT/.env"
  echo "Run scripts/oneclick-configure.sh first to create your .env"
fi

echo "==> Building and launching containers using $COMPOSE_FILE ..."

if [[ "$MODE" == "full" ]]; then
  ( cd "$REPO_ROOT" && docker compose -f "$COMPOSE_FILE" up -d --build )
else
  ( cd "$REPO_ROOT" && docker compose -f "$COMPOSE_FILE" up --build )
fi

URL="http://localhost:8080/api/docs"
echo "==> Opening API docs at $URL"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" || true
elif command -v open >/dev/null 2>&1; then
  open "$URL" || true
fi

echo "==> Done. API docs at $URL (landing page at http://localhost:8080)"
