# Requires: Python on PATH, repo root as current directory
# Uses OPENROUTER_API_KEY from environment or falls back to parsing .env
# Logs per-model-per-tier outputs to artifacts/tier_runs/<timestamp>/*.log

$ErrorActionPreference = 'Stop'

# Resolve and create output directory
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$baseOut = Join-Path (Get-Location) "artifacts\tier_runs\$timestamp"
New-Item -ItemType Directory -Force -Path $baseOut | Out-Null

# Ensure OpenRouter key is available
if (-not $env:OPENROUTER_API_KEY) {
  $envFile = Join-Path (Get-Location) ".env"
  if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
      if ($_ -match '^\s*OPENROUTER_API_KEY=(.+)$') {
        $env:OPENROUTER_API_KEY = $Matches[1].Trim()
      }
    }
  }
}
if (-not $env:OPENROUTER_API_KEY) {
  Write-Error "OPENROUTER_API_KEY not set. Set it or add to .env"
  exit 1
}

# Python path for local imports
$env:PYTHONPATH = (Get-Location).Path
# Reasonable timeout for OpenRouter requests
$env:REQUEST_TIMEOUT_SECONDS = "90"

# Model list to exercise
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

# Tiers to run
$tiers = @("T0","T1","T2")

Write-Host "Output directory: $baseOut"
Write-Host "Starting Tier runs..." -ForegroundColor Cyan

foreach ($m in $models) {
  $env:MODEL_SLUG = $m
  # Sanitize for filename
  $modelSan = ($m -replace '[^\w\.-]+','_')
  foreach ($t in $tiers) {
    $log = Join-Path $baseOut "$($modelSan)__$t.log"
    Write-Host ("[{0}] Running {1} for {2}" -f ((Get-Date).ToString("HH:mm:ss")), $t, $m) -ForegroundColor Yellow

    try {
      # Invoke Python runner with explicit args
      & python "integration_tests\run_integration_tests.py" --tier $t --model $m --verbose 2>&1 | Tee-Object -FilePath $log
      $exitCode = $LASTEXITCODE
    } catch {
      $_ | Out-String | Tee-Object -FilePath $log
      $exitCode = 1
    }

    if ($exitCode -eq 0) {
      Write-Host ("[{0}] Completed {1} for {2} (OK)" -f ((Get-Date).ToString("HH:mm:ss")), $t, $m) -ForegroundColor Green
    } else {
      Write-Host ("[{0}] Completed {1} for {2} (FAILED, see {3})" -f ((Get-Date).ToString("HH:mm:ss")), $t, $m, $log) -ForegroundColor Red
    }
  }
}

Write-Host "All runs finished. Logs in: $baseOut" -ForegroundColor Cyan