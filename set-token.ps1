# VibeForge Authentication Token Setup
# Run this script in each terminal session before starting services:
#   . .\set-token.ps1

param(
    [switch]$Generate,
    [string]$Token
)

$tokenFile = ".vibeforge-token"

# Generate new token
if ($Generate) {
    Write-Host "Generating new authentication token..." -ForegroundColor Yellow
    $newToken = python -c "import secrets; print(secrets.token_hex(32))"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to generate token. Is Python installed?" -ForegroundColor Red
        exit 1
    }

    # Save to file
    $newToken | Out-File -FilePath $tokenFile -NoNewline
    Write-Host "Token generated and saved to $tokenFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Copy this token to other machines!" -ForegroundColor Yellow
    Write-Host "Token: $newToken" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "On other machines, run:" -ForegroundColor Yellow
    Write-Host "  . .\set-token.ps1 -Token `"$newToken`"" -ForegroundColor Cyan

    $env:VIBEFORGE_AUTH_TOKEN = $newToken
    $env:VITE_CONTROL_TOKEN = $newToken
    exit 0
}

# Set specific token
if ($Token) {
    Write-Host "Setting authentication token from parameter..." -ForegroundColor Yellow
    $Token | Out-File -FilePath $tokenFile -NoNewline
    $env:VIBEFORGE_AUTH_TOKEN = $Token
    $env:VITE_CONTROL_TOKEN = $Token
    Write-Host "Token set successfully!" -ForegroundColor Green
    Write-Host "VIBEFORGE_AUTH_TOKEN: $($Token.Substring(0,16))..." -ForegroundColor Cyan
    exit 0
}

# Load existing token
if (Test-Path $tokenFile) {
    $existingToken = (Get-Content $tokenFile -Raw).Trim()

    if ([string]::IsNullOrWhiteSpace($existingToken)) {
        Write-Host "Error: Token file exists but is empty" -ForegroundColor Red
        Write-Host "Run: . .\set-token.ps1 -Generate" -ForegroundColor Yellow
        exit 1
    }

    $env:VIBEFORGE_AUTH_TOKEN = $existingToken
    $env:VITE_CONTROL_TOKEN = $existingToken
    Write-Host "Environment variables set from $tokenFile" -ForegroundColor Green
    Write-Host "VIBEFORGE_AUTH_TOKEN: $($existingToken.Substring(0,16))..." -ForegroundColor Cyan
    exit 0
}

# No token found
Write-Host "No token found. Please generate a token first:" -ForegroundColor Yellow
Write-Host ""
Write-Host "To generate a new token:" -ForegroundColor Cyan
Write-Host "  . .\set-token.ps1 -Generate" -ForegroundColor White
Write-Host ""
Write-Host "To use an existing token from another machine:" -ForegroundColor Cyan
Write-Host "  . .\set-token.ps1 -Token `"your-token-here`"" -ForegroundColor White
Write-Host ""
exit 1
