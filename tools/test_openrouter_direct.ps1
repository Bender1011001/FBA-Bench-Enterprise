# Read API key from .env
$envLine = Get-Content .env | Where-Object { $_ -match '^OPENROUTER_API_KEY=' }
if ($envLine) {
    $key = $envLine.Split('=')[1].Trim()
    if ($key.StartsWith('"') -and $key.EndsWith('"')) { $key = $key.Substring(1, $key.Length - 2).Trim() }
    elseif ($key.StartsWith("'") -and $key.EndsWith("'")) { $key = $key.Substring(1, $key.Length - 2).Trim() }
} else {
    Write-Output "Error: OPENROUTER_API_KEY not found in .env"
    exit 1
}

$headers = @{
    'Authorization' = "Bearer $key"
    'HTTP-Referer' = 'http://localhost:3000'
    'X-Title' = 'FBA-Bench Dev'
    'Content-Type' = 'application/json'
}

$body = @{
    model = 'x-ai/grok-4-fast:free'
    messages = @(
        @{
            role = 'user'
            content = 'Hello'
        }
    )
} | ConvertTo-Json -Depth 3

try {
    $response = Invoke-RestMethod -Uri 'https://openrouter.ai/api/v1/chat/completions' -Method Post -Headers $headers -Body $body
    Write-Output "Success: $($response | ConvertTo-Json -Depth 3)"
} catch {
    $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 'Unknown' }
    $errorMsg = $_.Exception.Message
    Write-Output "Error: $errorMsg Status: $statusCode"
    if ($_.Exception.Response) {
        $errorContent = $_.Exception.Response | Get-Content -Raw
        Write-Output "Response Body: $errorContent"
    }
}