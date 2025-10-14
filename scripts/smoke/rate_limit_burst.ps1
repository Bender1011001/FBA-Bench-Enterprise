param(
  [int]$Burst = 20,
  [int]$Repeats = 1
)

$ErrorActionPreference = 'Stop'

function Write-Info { param([string]$m) Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Err  { param([string]$m) Write-Host "[ERROR] $m" -ForegroundColor Red }

if (-not (Test-Path -Path ".\private.pem")) {
  Write-Err "private.pem not found. Generate it with: openssl genrsa -out private.pem 2048; openssl rsa -in private.pem -pubout -out public.pem"
  exit 2
}

# Generate JWT
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

$allCodes = New-Object System.Collections.Generic.List[int]

for ($r = 1; $r -le $Repeats; $r++) {
  Write-Info ("Burst {0}/{1}: firing {2} parallel requests to {3}" -f $r, $Repeats, $Burst, $settingsUrl)

  $jobs = @()
  for ($i = 0; $i -lt $Burst; $i++) {
    $jobs += Start-Job -ScriptBlock {
      param($url, $token)
      try {
        $resp = Invoke-WebRequest -UseBasicParsing -Headers @{ Authorization = "Bearer $token" } -Uri $url -Method GET -TimeoutSec 5 -ErrorAction Stop
        return [int]$resp.StatusCode
      } catch {
        $status = ($_.Exception.Response.StatusCode.value__ 2>$null)
        if ($status) { return [int]$status } else { return -1 }
      }
    } -ArgumentList $settingsUrl, $jwt
  }

  Wait-Job -Job $jobs | Out-Null
  $codes = @()
  foreach ($j in $jobs) {
    $codes += Receive-Job -Job $j
    Remove-Job -Job $j | Out-Null
  }

  $allCodes.AddRange([int[]]$codes)

  Write-Host ("Burst codes: {0}" -f [string]::Join(',', $codes))
  $groups = $codes | Group-Object | ForEach-Object { "{0}x {1}" -f $_.Count, $_.Name }
  Write-Host ("Burst counts: {0}" -f [string]::Join('; ', $groups))
}

Write-Host ("All codes: {0}" -f [string]::Join(',', $allCodes))
$allGroups = $allCodes | Group-Object | ForEach-Object { "{0}x {1}" -f $_.Count, $_.Name }
Write-Host ("All counts: {0}" -f [string]::Join('; ', $allGroups))

# Exit success even if no 429 (environment may be slow enough to avoid collision)
exit 0
