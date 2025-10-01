# deploy_sandbox.ps1 - Dry-run Terraform planning for managed sandbox
# Usage: powershell -ExecutionPolicy Bypass -File deploy_sandbox.ps1 [-VarFile <string>]
#   VarFile: Optional .tfvars file (default: tenant.tfvars)
# This script performs terraform init, validate, and plan only.
# No resources are created or destroyed. Run from repository root.

param(
    [string]$VarFile = "tenant.tfvars"
)

# Determine script directory and repository root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Split-Path -Parent $ScriptDir
$TfDir = Join-Path $RepoRoot "terraform"

# Check if Terraform is installed
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Error "Terraform is not installed or not in PATH. Install from https://www.terraform.io/downloads.html"
    exit 1
}

# Check if var file exists
$VarFilePath = Join-Path $TfDir $VarFile
if (-not (Test-Path $VarFilePath)) {
    Write-Warning "$VarFile not found in $TfDir. Copy terraform.tfvars.example to tenant.tfvars and customize."
    Write-Warning "Creating a basic tenant.tfvars from example..."
    Copy-Item (Join-Path $TfDir "terraform.tfvars.example") $VarFilePath
}

# Change to Terraform directory
Set-Location $TfDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "Cannot cd to $TfDir"
    exit 1
}

Write-Output "=== Initializing Terraform (providers only, no cloud credentials needed) ==="
terraform init -upgrade

Write-Output "=== Validating Terraform configuration ==="
terraform validate

Write-Output "=== Planning managed sandbox (dry-run, no changes applied) ==="
terraform plan -var-file=$VarFile -out=plan.out -compact-warnings

Write-Output "=== Plan complete! ==="
Write-Output "No resources were created. To review the plan:"
Write-Output "  terraform show plan.out"
Write-Output "To apply (future step - not in this script):"
Write-Output "  terraform apply plan.out"
Write-Output "Safety note: This skeleton uses only local/random/null providers; extend for cloud in future steps."