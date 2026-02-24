# Security Fix Script for Agentic Trader Frontend (PowerShell)
#
# This script helps identify and fix common security issues.
#
# Usage: .\scripts\security-fix.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Agentic Trader - Security Fix Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
Write-Host "[1/5] Checking environment configuration..."
if (!(Test-Path ".env")) {
    Write-Host "[!] .env file not found!" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[✓] Created .env from .env.example" -ForegroundColor Green
        Write-Host "[!] Please edit .env and fill in your actual values!" -ForegroundColor Yellow
    } else {
        Write-Host "[✗] .env.example not found! Cannot create .env" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[✓] .env file exists" -ForegroundColor Green
}

# Check for hardcoded credentials
Write-Host ""
Write-Host "[2/5] Scanning for hardcoded credentials..."
$CredentialsFound = $false

# Check for Auth0 credentials in source
$Auth0Matches = Select-String -Path "src\*.tsx", "src\*.ts" -Pattern "auth0\.com" -Exclude ".env" -ErrorAction SilentlyContinue
if ($Auth0Matches) {
    Write-Host "[✗] Found hardcoded Auth0 domain in source code!" -ForegroundColor Red
    $Auth0Matches | ForEach-Object { Write-Host $_.Line }
    $CredentialsFound = $true
}

if (-not $CredentialsFound) {
    Write-Host "[✓] No hardcoded credentials found in source code" -ForegroundColor Green
}

# Check for localStorage token storage
Write-Host ""
Write-Host "[3/5] Checking for insecure token storage..."
$TokenMatches = Select-String -Path "src\*.tsx", "src\*.ts" -Pattern "localStorage.*token" -ErrorAction SilentlyContinue
if ($TokenMatches) {
    Write-Host "[!] Found localStorage token storage (should use httpOnly cookies)" -ForegroundColor Yellow
    $TokenMatches | ForEach-Object { Write-Host $_.Line }
} else {
    Write-Host "[✓] No insecure localStorage token storage found" -ForegroundColor Green
}

# Run npm audit
Write-Host ""
Write-Host "[4/5] Running npm audit..."
npm audit --audit-level=moderate

# Check for security updates
Write-Host ""
Write-Host "[5/5] Checking for security updates..."
npm outdated

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Security Check Complete" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($CredentialsFound) {
    Write-Host "[✗] CRITICAL: Hardcoded credentials found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To fix:"
    Write-Host "  1. Move all credentials to .env file"
    Write-Host "  2. Use import.meta.env.VITE_* to access them"
    Write-Host "  3. Never commit .env to git"
    Write-Host ""
} else {
    Write-Host "[✓] No critical security issues found" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Review .env file and fill in your values"
    Write-Host "  2. Run: npm audit fix"
    Write-Host "  3. Ensure .env is in .gitignore"
    Write-Host ""
}
