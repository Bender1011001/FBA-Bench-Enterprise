# Thin wrapper to run the tenant env generator Python script.
# Usage: .\generate_tenant_env.ps1 [args] (same as python generate_tenant_env.py)

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonScript = Join-Path $ScriptDir "generate_tenant_env.py"

if (-not (Test-Path $PythonScript)) {
    Write-Error "Python script not found at $PythonScript"
    exit 1
}

python $PythonScript @Args