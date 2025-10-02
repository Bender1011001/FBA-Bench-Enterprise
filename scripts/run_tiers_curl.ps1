# Runs minimal Tier T0/T1/T2 checks for each model via OpenRouter using Invoke-RestMethod (no brittle quoting)
# Requires OPENROUTER_API_KEY in environment or .env in repo root
# Writes per-run JSON artifacts to artifacts/tier_runs_curl/<timestamp>/<model>__<tier>.json

$ErrorActionPreference = 'Stop'

# Resolve repo root (script is under scripts/)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Ensure key present (robust .env parsing + quote stripping)
if (-not $env:OPENROUTER_API_KEY) {
  $envPath = Join-Path $root ".env"
  if (Test-Path $envPath) {
    foreach ($line in Get-Content $envPath) {
      if ($line -match '^\s*OPENROUTER_API_KEY\s*=\s*(.+)$') {
        $val = $Matches[1].Trim()
        # Strip surrounding quotes if present
        if ($val -match '^\s*"(.*)"\s*$') { $val = $Matches[1] }
        elseif ($val -match "^\s*'(.*)'\s*$") { $val = $Matches[1] }
        $env:OPENROUTER_API_KEY = $val.Trim()
      }
    }
  }
}
if (-not $env:OPENROUTER_API_KEY) {
  Write-Error "OPENROUTER_API_KEY not set. Set it or add it to .env"
  exit 1
}
# Normalize key in case of stray quotes/whitespace
$env:OPENROUTER_API_KEY = $env:OPENROUTER_API_KEY.Trim()
if ($env:OPENROUTER_API_KEY -match '^\s*"(.*)"\s*$') { $env:OPENROUTER_API_KEY = $Matches[1] }
elseif ($env:OPENROUTER_API_KEY -match "^\s*'(.*)'\s*$") { $env:OPENROUTER_API_KEY = $Matches[1] }

# Headers recommended by OpenRouter (include Referer variants for proxy quirks)
$headers = @{
  Authorization  = "Bearer $($env:OPENROUTER_API_KEY)"
  "X-Title"      = "FBA-Bench"
  "HTTP-Referer" = "https://github.com/"
  "Referer"      = "https://github.com/"
}

# Preflight auth check to catch 401 early with helpful diagnostics
try {
  $null = Invoke-RestMethod -Method Get -Uri "https://openrouter.ai/api/v1/models" -Headers $headers
}
catch {
  $prefix = if ($env:OPENROUTER_API_KEY.Length -ge 6) { $env:OPENROUTER_API_KEY.Substring(0,6) } else { $env:OPENROUTER_API_KEY }
  $suffix = if ($env:OPENROUTER_API_KEY.Length -ge 4) { $env:OPENROUTER_API_KEY.Substring($env:OPENROUTER_API_KEY.Length-4) } else { "" }
  $masked = "$prefix***$suffix"
  Write-Error ("Preflight auth failed: {0}. Check OPENROUTER_API_KEY={1} and ensure it is valid and unquoted in .env." -f $_.Exception.Message, $masked)
  exit 1
}

# Helper: robust POST to OpenRouter chat/completions with detailed error capture and curl.exe fallback on 401
function Invoke-OpenRouterChat([hashtable]$headers, [string]$json) {
  try {
    return Invoke-RestMethod -Method Post -Uri "https://openrouter.ai/api/v1/chat/completions" -Headers $headers -Body $json -ContentType "application/json"
  }
  catch {
    $status = $null
    $respBody = $null
    if ($_.Exception.PSObject.Properties.Name -contains 'Response' -and $_.Exception.Response) {
      try { $status = $_.Exception.Response.StatusCode.Value__ } catch {}
      try {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $respBody = $reader.ReadToEnd()
        $reader.Dispose()
        $stream.Dispose()
      } catch {}
    }
    if ($status -eq 401) {
      # Fallback to curl.exe with a temp JSON file to avoid any PS body/encoding quirks
      $tmp = Join-Path $env:TEMP ("openrouter_req_{0}.json" -f ([System.Guid]::NewGuid().ToString("N")))
      $json | Out-File -FilePath $tmp -Encoding UTF8
      $curlHeaders = @(
        "-H", "Authorization: Bearer $($env:OPENROUTER_API_KEY)",
        "-H", "Content-Type: application/json",
        "-H", "X-Title: FBA-Bench",
        "-H", "HTTP-Referer: https://github.com/",
        "-H", "Referer: https://github.com/"
      )
      $args = @("-sS", "-X", "POST", "https://openrouter.ai/api/v1/chat/completions") + $curlHeaders + @("--data-binary", "@$tmp")
      $out = & curl.exe @args 2>&1
      Remove-Item -Force $tmp
      try {
        return $out | ConvertFrom-Json
      } catch {
        $msg = "401 via Invoke-RestMethod; curl fallback also failed. Response: $respBody; curl out: $out"
        throw $msg
      }
    }
    else {
      if ($respBody) { throw "$($_.Exception.Message) | body: $respBody" }
      throw
    }
  }
}

# Output dir
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = Join-Path $root "artifacts\tier_runs_curl\$timestamp"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Models to run
$models = @(
  "x-ai/grok-4-fast:free",
  "deepseek/deepseek-chat-v3.1:free",
  "deepseek/deepseek-r1-0528:free",
  "qwen/qwen3-coder:free",
  "google/gemini-2.0-flash-exp:free",
  "meta-llama/llama-3.3-70b-instruct:free",
  "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
  "openai/gpt-oss-20b:free",
  "moonshotai/kimi-k2:free",
  "cognitivecomputations/dolphin3.0-mistral-24b:free",
  "openai/gpt-oss-120b:free"
)

# Tiers
$tiers = @("T0","T1","T2")

# Allow environment overrides for models and tiers (comma-separated)
if ($env:MODELS -and $env:MODELS.Trim().Length -gt 0) {
  $models = $env:MODELS.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
}
if ($env:TIERS -and $env:TIERS.Trim().Length -gt 0) {
  $tiers = $env:TIERS.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
}

function Sanitize([string]$s) {
  return ($s -replace '[^\w\.-]+','_')
}

Write-Host "Artifacts: $outDir" -ForegroundColor Cyan
$total = 0; $ok=0; $mismatch=0; $errors=0
$summary = @()

foreach ($m in $models) {
  foreach ($t in $tiers) {
    $total++
    $prompt = "Return exactly OK_$t and nothing else."

    $body = @{
      model = $m
      messages = @(@{ role = "user"; content = $prompt })
      temperature = 0
      max_tokens = 32
      response_format = @{ type = "text" }
    }
    $json = $body | ConvertTo-Json -Depth 6

    $fn = Join-Path $outDir ("{0}__{1}.json" -f (Sanitize $m), $t)
    Write-Host ("[{0}] {1} : {2}" -f (Get-Date -Format HH:mm:ss), $t, $m) -ForegroundColor Yellow
    try {
      $resp = Invoke-OpenRouterChat -headers $headers -json $json
      $content = ""
      if ($resp -and $resp.choices -and $resp.choices.Count -gt 0) {
        $choice = $resp.choices[0]
        if ($choice.message -and $choice.message.content) {
          $content = [string]$choice.message.content
        }
        elseif ($choice.text) {
          $content = [string]$choice.text
        }
        elseif ($choice.delta -and $choice.delta.content) {
          $content = [string]$choice.delta.content
        }
      }
      $status = "mismatch"
      if ($content.TrimStart().StartsWith("OK_$t")) { $status = "ok" }

      $obj = [ordered]@{
        model       = $m
        tier        = $t
        status      = $status
        content     = $content
        provider    = $resp.provider
        model_used  = $resp.model
        usage       = $resp.usage
        raw_response= $resp
      }
      $obj | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 -FilePath $fn

      if ($status -eq "ok") {
        $ok++
        Write-Host " -> OK" -ForegroundColor Green
      }
      else {
        $mismatch++
        Write-Host (" -> MISMATCH: '{0}'" -f ($content -replace "`r?`n"," " -replace '\s+',' ').Substring(0, [Math]::Min(80,[Math]::Max(0, ($content -replace "`r?`n"," ").Length)))) -ForegroundColor DarkYellow
      }
      $summary += $obj
    }
    catch {
      $errors++
      $detail = $null
      if ($_.Exception.PSObject.Properties.Name -contains 'Message') { $detail = $_.Exception.Message }
      $errObj = [ordered]@{
        model  = $m
        tier   = $t
        status = "error"
        error  = $detail
      }
      $errObj | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 -FilePath $fn
      Write-Host (" -> ERROR: {0}" -f $detail) -ForegroundColor Red
    }
  }
}

# Write summary
$summaryPath = Join-Path $outDir "summary.json"
$summary | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 -FilePath $summaryPath

Write-Host ""
Write-Host ("Completed: total={0}, ok={1}, mismatch={2}, errors={3}" -f $total,$ok,$mismatch,$errors) -ForegroundColor Cyan
Write-Host ("Summary: {0}" -f $summaryPath) -ForegroundColor Cyan