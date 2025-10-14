#!/usr/bin/env bash
# FBA-Bench Docker Setup Script (Compose v2 and v1 compatible)
# Starts/stops services defined in docker-compose.yml at the repo root.
# Aligns with service name: "api" (FastAPI).

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Resolve docker compose command (plugin preferred)
resolve_dc_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    print_error "Docker Compose is not installed. Install Docker Desktop or docker-compose."
    print_status "See https://docs.docker.com/compose/install/"
    exit 1
  fi
}

# Pre-flight checks
if ! command -v docker >/dev/null 2>&1; then
  print_error "Docker is not installed. Install Docker first."
  print_status "See https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  print_error "Docker is not running. Start Docker and try again."
  exit 1
fi

DC_CMD="$(resolve_dc_cmd)"

# Optional data dirs (not strictly required)
mkdir -p scenario_results logs

start_services() {
  print_status "Starting FBA-Bench services via: ${DC_CMD}"
  ${DC_CMD} up --build -d

  # Lightweight readiness check: wait for API to accept connections.
  # Health endpoint may return 200 or 503 (e.g., when Redis isn't present).
  local url="http://localhost:8000/api/v1/health"
  print_status "Waiting for API to respond at ${url} ..."
  local ready=0
  for i in {1..30}; do
    # Accept any HTTP response as "ready" (200 OK or 5xx from known health behavior)
    code="$(curl -s -o /dev/null -w '%{http_code}' "${url}" || true)"
    if [[ "${code}" =~ ^[0-9]{3}$ ]]; then
      print_success "API responded (HTTP ${code})."
      ready=1
      break
    fi
    sleep 2
  done
  if [[ "${ready}" -ne 1 ]]; then
    print_warning "API did not respond within 60s. Use '${DC_CMD} logs api' to inspect."
  fi

  echo
  print_success "FBA-Bench services are up."
  print_status "API:      http://localhost:8000  (Docs may be gated in protected envs)"
  echo
  print_status "View logs: ${DC_CMD} logs -f api"
  print_status "Stop:      $0 stop"
}

stop_services() {
  print_status "Stopping services..."
  ${DC_CMD} down
  print_success "Services stopped."
}

show_logs() {
  if [[ -n "${2:-}" ]]; then
    ${DC_CMD} logs -f "$2"
  else
    ${DC_CMD} logs -f
  fi
}

reset_installation() {
  print_warning "This will remove containers, networks, and volumes created by Compose."
  read -p "Proceed? (y/N): " -r ans
  echo
  if [[ "${ans}" =~ ^[Yy]$ ]]; then
    print_status "Removing all Compose artifacts..."
    ${DC_CMD} down -v
    print_success "Reset completed."
  else
    print_status "Reset cancelled."
  fi
}

update_installation() {
  print_status "Updating repository (git pull) and rebuilding images..."
  if command -v git >/dev/null 2>&1; then
    git pull || print_warning "git pull failed or no git repo. Continuing."
  else
    print_warning "git not installed; skipping pull."
  fi
  ${DC_CMD} build --no-cache
  ${DC_CMD} up -d
  print_success "Services updated and running."
}

case "${1:-start}" in
  start)   start_services ;;
  stop)    stop_services ;;
  restart) stop_services; start_services ;;
  logs)    show_logs "$@" ;;
  reset)   reset_installation ;;
  update)  update_installation ;;
  status)  ${DC_CMD} ps ;;
  *)
    echo "FBA-Bench Docker Setup Script"
    echo
    echo "Usage: $0 {start|stop|restart|logs|reset|update|status}"
    echo
    echo "Commands:"
    echo "  start     Start services (default)"
    echo "  stop      Stop services"
    echo "  restart   Restart services"
    echo "  logs      Show logs (optionally specify service: api)"
    echo "  reset     Remove all containers, networks, and volumes"
    echo "  update    git pull + rebuild images + up -d"
    echo "  status    Show Compose status"
    exit 1
    ;;
esac
