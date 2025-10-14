Param()

$ErrorActionPreference = "Stop"

# Determine repo root (parent of scripts directory)
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$envFile  = Join-Path $repoRoot ".env"

Write-Host "==> One-time configuration: creating/updating $envFile"

# Prompt for optional API keys
$openai     = Read-Host "OpenAI API Key (optional)"
$anthropic  = Read-Host "Anthropic API Key (optional)"
$google     = Read-Host "Google API Key (optional)"
$cohere     = Read-Host "Cohere API Key (optional)"
$openrouter = Read-Host "OpenRouter API Key (optional)"

# Compose .env content
$envContent = @"
# --- LLM API Keys (optional) ---
OPENAI_API_KEY=$openai
ANTHROPIC_API_KEY=$anthropic
GOOGLE_API_KEY=$google
COHERE_API_KEY=$cohere
OPENROUTER_API_KEY=$openrouter

# --- Backend Runtime ---
# Internal Redis for realtime pub/sub
FBA_BENCH_REDIS_URL=redis://redis:6379/0

# Persist SQLite DB to a mounted volume in the api container
DATABASE_URL=sqlite:////data/fba_bench.db

# --- Auth (disabled by default for one-click) ---
AUTH_ENABLED=false
AUTH_TEST_BYPASS=true
FBA_CORS_ALLOW_ORIGINS=http://localhost:8080
"@

# Write .env (UTF-8 without BOM)
Set-Content -Path $envFile -Value $envContent -Encoding UTF8 -NoNewline
Write-Host "==> Wrote $envFile"
