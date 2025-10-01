#!/bin/bash
# deploy_sandbox.sh - Dry-run Terraform planning for managed sandbox
# Usage: bash deploy_sandbox.sh [var_file]
#   var_file: Optional .tfvars file (default: tenant.tfvars)
# This script performs terraform init, validate, and plan only.
# No resources are created or destroyed. Run from repository root.

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Determine script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
TF_DIR="$REPO_ROOT/terraform"

# Check if Terraform is installed
if ! command -v terraform &>/dev/null; then
  echo "Error: Terraform is not installed or not in PATH. Install from https://www.terraform.io/downloads.html" >&2
  exit 1
fi

# Default var file
VAR_FILE="${1:-tenant.tfvars}"

# Check if var file exists
if [[ ! -f "$TF_DIR/$VAR_FILE" ]]; then
  echo "Warning: $VAR_FILE not found in $TF_DIR. Copy terraform.tfvars.example to tenant.tfvars and customize." >&2
  echo "Creating a basic tenant.tfvars from example..." >&2
  cp "$TF_DIR/terraform.tfvars.example" "$TF_DIR/tenant.tfvars"
fi

# Change to Terraform directory
cd "$TF_DIR" || { echo "Error: Cannot cd to $TF_DIR" >&2; exit 1; }

echo "=== Initializing Terraform (providers only, no cloud credentials needed) ==="
terraform init -upgrade

echo "=== Validating Terraform configuration ==="
terraform validate

echo "=== Planning managed sandbox (dry-run, no changes applied) ==="
terraform plan -var-file="$VAR_FILE" -out=plan.out -compact-warnings

echo "=== Plan complete! ==="
echo "No resources were created. To review the plan:"
echo "  terraform show plan.out"
echo "To apply (future step - not in this script):"
echo "  terraform apply plan.out"
echo "Safety note: This skeleton uses only local/random/null providers; extend for cloud in future steps."