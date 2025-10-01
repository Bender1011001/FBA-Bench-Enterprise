param(
  [Parameter(Mandatory = $true)]
  [string]$Tenant,

  [string]$Domain,
  [string]$Env,
  [string]$ApiUrl,
  [string]$WebUrl,
  [string]$StripePublicKey,
  [string]$PriceId,
  [string]$JwtSecret,
  [string]$StripeSecretKey,
  [string]$StripeWebhookSecret,
  [string]$ApiImageTag,
  [string]$WebImageTag,
  [string]$OutDir,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

# Check for Python
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    $pythonPath = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $pythonPath) {
    Write-Error "Python is required but not found in PATH. Install Python 3 and ensure it's accessible."
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = Join-Path $ScriptDir "generate_tenant_configs.py"

# Change to repo root (assuming script is in infrastructure/scripts/)
$RepoRoot = (Get-Item $ScriptDir).Parent.Parent.Parent
Set-Location $RepoRoot

$argsList = @("--tenant", $Tenant)

if ($Domain) { $argsList += @("--domain", $Domain) }
if ($Env) { $argsList += @("--env", $Env) }
if ($ApiUrl) { $argsList += @("--api-url", $ApiUrl) }
if ($WebUrl) { $argsList += @("--web-url", $WebUrl) }
if ($StripePublicKey) { $argsList += @("--stripe-public-key", $StripePublicKey) }
if ($PriceId) { $argsList += @("--price-id", $PriceId) }
if ($JwtSecret) { $argsList += @("--jwt-secret", $JwtSecret) }
if ($StripeSecretKey) { $argsList += @("--stripe-secret-key", $StripeSecretKey) }
if ($StripeWebhookSecret) { $argsList += @("--stripe-webhook-secret", $StripeWebhookSecret) }
if ($ApiImageTag) { $argsList += @("--api-image-tag", $ApiImageTag) }
if ($WebImageTag) { $argsList += @("--web-image-tag", $WebImageTag) }
if ($OutDir) { $argsList += @("--out-dir", $OutDir) }
if ($Force.IsPresent) { $argsList += @("--force") }

& $pythonPath $Py @argsList