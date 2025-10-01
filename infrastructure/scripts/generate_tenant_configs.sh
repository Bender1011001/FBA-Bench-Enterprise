#!/usr/bin/env bash
set -euo pipefail

# Detect Python3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is required but not found. Install Python 3 and ensure it's in PATH." >&2
    exit 1
fi

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <tenant_slug> [options]"
    echo "  <tenant_slug>: Required tenant identifier (e.g., 'demo'; [a-z0-9-]+)"
    echo "  Options: --domain=<value> --env=<value> --api-url=<value> --web-url=<value>"
    echo "           --stripe-public-key=<value> --price-id=<value> --jwt-secret=<value>"
    echo "           --stripe-secret-key=<value> --stripe-webhook-secret=<value>"
    echo "           --api-image-tag=<value> --web-image-tag=<value> --out-dir=<path> --force"
    echo "Run from repository root (c:/Users/admin/Downloads/fba)."
    echo "Defaults applied for unspecified options; see python script for details."
    exit 1
fi

TENANT="$1"
shift

# Resolve script dir relative to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/generate_tenant_configs.py"

# Run from repo root context (adjust if needed; assumes cwd is root)
cd "$(dirname "$SCRIPT_DIR")/../.." || { echo "ERROR: Failed to change to repo root" >&2; exit 1; }

python3 "$PY_SCRIPT" --tenant "$TENANT" "$@"