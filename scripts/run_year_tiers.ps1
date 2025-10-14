Continue = 'Stop'
 = Get-Date -Format 'yyyyMMdd_HHmmss'
 = Join-Path (Get-Location) 'artifacts\year_runs\' + 
New-Item -ItemType Directory -Force -Path  | Out-Null

# year-like simulation pacing (set once)
 = '365'
 = '0.01'
 = '200'

 = @(
  'x-ai/grok-4-fast:free',
  'deepseek/deepseek-chat-v3.1:free',
  'deepseek/deepseek-r1-0528:free',
  'qwen/qwen3-coder:free',
  'google/gemini-2.0-flash-exp:free',
  'meta-llama/llama-3.3-70b-instruct:free',
  'cognitivecomputations/dolphin-mistral-24b-venice-edition:free',
  'openai/gpt-oss-20b:free',
  'moonshotai/kimi-k2:free',
  'cognitivecomputations/dolphin3.0-mistral-24b:free',
  'openai/gpt-oss-120b:free'
)

 = @('T0','T1')
Write-Host 'Output: ' 

foreach ( in ) {
  foreach ( in ) {
     = ( -replace '[^\w\.-]+','_')
     = Join-Path  ( + '__' +  + '.log')
    Write-Host ('[' + (Get-Date).ToString('HH:mm:ss') + '] Running ' +  + ' for ' + ) -ForegroundColor Yellow

    poetry run python integration_tests/run_integration_tests.py --tier  --model  --verbose --max-ticks 365 --tick-interval-seconds 0.01 --time-acceleration 200 2>&1 | Tee-Object -FilePath 
    if ( -eq 0) {
      Write-Host ('OK: ' +  + ' ' + ) -ForegroundColor Green
    } else {
      Write-Host ('FAIL: ' +  + ' ' +  + ' (see ' +  + ')') -ForegroundColor Red
    }
  }
}
Write-Host ('All runs finished. Logs at: ' + ) -ForegroundColor Cyan
