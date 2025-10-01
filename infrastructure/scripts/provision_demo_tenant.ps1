# PowerShell script for demo tenant dry-run provisioning
param(
    [string]$Tenant = "demo",
    [string]$Domain = "demo.example.com",
    [string]$ApiUrl = "http://localhost:8000",
    [string]$WebUrl = "http://localhost:5173",
    [string]$StripePublicKey = "pk_test_CHANGE_ME",
    [string]$PriceId = "price_123CHANGE_ME",
    [string]$JwtSecret = "CHANGE_ME_DEV",
    [string]$ApiImageTag = "latest",
    [string]$WebImageTag = "latest",
    [switch]$Force
)

# Resolve repo root: walk up from script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = (Get-Item $ScriptDir).Parent.Parent.Parent.FullName

# Change to repo root
Set-Location $RepoRoot

# Check dependencies
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is required but not found in PATH." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Terraform is required but not found in PATH." -ForegroundColor Red
    exit 1
}

# Generate tenant configs
$ForceArg = if ($Force) { "--force" } else { "" }

Write-Host "Generating tenant configs for '$Tenant'..."
& python "infrastructure/scripts/generate_tenant_configs.py" `
    --tenant $Tenant `
    --domain $Domain `
    --api-url $ApiUrl `
    --web-url $WebUrl `
    --stripe-public-key $StripePublicKey `
    --price-id $PriceId `
    --jwt-secret $JwtSecret `
    --api-image-tag $ApiImageTag `
    --web-image-tag $WebImageTag `
    $ForceArg

# Run Terraform dry-run
$TfDir = Join-Path $RepoRoot "infrastructure/terraform"
Set-Location $TfDir

Write-Host "Initializing Terraform..."
terraform init -upgrade

Write-Host "Validating Terraform configuration..."
terraform validate

Write-Host "Running Terraform plan..."
terraform plan `
    -var-file "../tenants/$Tenant/terraform.tfvars" `
    -out "plan-$Tenant.out" `
    -compact-warnings

Set-Location $RepoRoot

# Print summary
Write-Host ""
Write-Host "=== Demo Provisioning Summary ===" -ForegroundColor Green
Write-Host "Tenant: $Tenant"
Write-Host "Generated config files:"
Write-Host "  - infrastructure/tenants/$Tenant/.env"
Write-Host "  - infrastructure/tenants/$Tenant/terraform.tfvars"
Write-Host "Terraform plan file:"
Write-Host "  - infrastructure/terraform/plan-$Tenant.out"
Write-Host ""
Write-Host "Dry-run complete. No resources were provisioned (no 'terraform apply' executed)."
Write-Host "To review the plan: terraform show infrastructure/terraform/plan-$Tenant.out"

exit 0