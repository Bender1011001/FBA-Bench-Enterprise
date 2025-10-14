param()

$ErrorActionPreference = 'Stop'

function Write-Info { param([string]$m) Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Success { param([string]$m) Write-Host "[SUCCESS] $m" -ForegroundColor Green }
function Write-Warn { param([string]$m) Write-Host "[WARNING] $m" -ForegroundColor Yellow }
function Write-Err { param([string]$m) Write-Host "[ERROR] $m" -ForegroundColor Red }

if (-not (Test-Path -Path ".\private.pem")) {
  Write-Err "private.pem not found. Generate it with: openssl genrsa -out private.pem 2048; openssl rsa -in private.pem -pubout -out public.pem"
  exit 2
}

try {
  $jwt = python .\scripts\smoke\jwt\gen_test_jwt.py --private-key .\private.pem --sub tester
} catch {
  Write-Err "Failed to run JWT generator: $($_.Exception.Message)"
  exit 2
}

$jwt = "$jwt".Trim()
if ([string]::IsNullOrWhiteSpace($jwt)) {
  Write-Err "JWT generation returned empty token"
  exit 2
}
Write-Info ("JWT length: {0}" -f $jwt.Length)

$settingsUrl = "http://127.0.0.1:8000/api/v1/settings"
$healthUrl   = "http://127.0.0.1:8000/api/v1/health"

$codes = New-Object System.Collections.Generic.List[int]
for ($i = 0; $i -lt 10; $i++) {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Headers @{ Authorization = "Bearer $jwt" } -Uri $settingsUrl -Method GET -TimeoutSec 5
    $codes.Add([int]$resp.StatusCode)
  } catch {
    $status = ($_.Exception.Response.StatusCode.value__ 2>$null)
    if ($status) { $codes.Add([int]$status) } else { $codes.Add(-1) }
  }
}
Write-Host ("Settings status codes: {0}" -f [string]::Join(',', $codes))
$settingsGroups = $codes | Group-Object | ForEach-Object { "{0}x {1}" -f $_.Count, $_.Name }
Write-Host ("Settings counts: {0}" -f [string]::Join('; ', $settingsGroups))

$hcodes = New-Object System.Collections.Generic.List[int]
for ($i = 0; $i -lt 30; $i++) {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -Method GET -TimeoutSec 5
    $hcodes.Add([int]$resp.StatusCode)
  } catch {
    $status = ($_.Exception.Response.StatusCode.value__ 2>$null)
    if ($status) { $hcodes.Add([int]$status) } else { $hcodes.Add(-1) }
  }
}
Write-Host ("Health status codes: {0}" -f [string]::Join(',', $hcodes))
$hgroups = $hcodes | Group-Object | ForEach-Object { "{0}x {1}" -f $_.Count, $_.Name }
Write-Host ("Health counts: {0}" -f [string]::Join('; ', $hgroups))

if ($hcodes -contains 429) {
  Write-Err "Health endpoint returned 429 (should be exempt)"
  exit 3
}
exit 0
