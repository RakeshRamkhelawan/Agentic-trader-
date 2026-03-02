# SSL Certificate Setup Script for Agentic Trader Platform
# Usage: .\setup_ssl.ps1 [domain]

param(
    [string]$Domain = "localhost"
)

$SSL_DIR = ".\nginx\ssl"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Agentic Trader Platform - SSL Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Domain: $Domain"
Write-Host "SSL Directory: $SSL_DIR"
Write-Host ""

# Create SSL directory
New-Item -ItemType Directory -Force -Path $SSL_DIR | Out-Null

# Check if openssl is installed
$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $openssl) {
    Write-Host "ERROR: openssl is not installed. Please install it first." -ForegroundColor Red
    Write-Host "You can install it via:"
    Write-Host "  - Chocolatey: choco install openssl"
    Write-Host "  - Download from: https://slproweb.com/products/Win32OpenSSL.html"
    exit 1
}

# Check if certificates already exist
$certExists = Test-Path "$SSL_DIR\cert.pem"
$keyExists = Test-Path "$SSL_DIR\key.pem"

if ($certExists -and $keyExists) {
    Write-Host "SSL certificates already exist."
    $regenerate = Read-Host "Do you want to regenerate them? (y/N)"
    if ($regenerate -notmatch '^[Yy]$') {
        Write-Host "Keeping existing certificates."
        exit 0
    }
}

Write-Host "Generating self-signed SSL certificates..."
Write-Host ""

# Generate private key
& openssl genrsa -out "$SSL_DIR\key.pem" 2048

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to generate private key" -ForegroundColor Red
    exit 1
}

# Generate certificate signing request
& openssl req -new -key "$SSL_DIR\key.pem" -out "$SSL_DIR\cert.csr" -subj "/CN=$Domain/O=Agentic Trader Platform/C=US"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to generate CSR" -ForegroundColor Red
    exit 1
}

# Generate self-signed certificate (valid for 365 days)
& openssl x509 -req -days 365 -in "$SSL_DIR\cert.csr" -signkey "$SSL_DIR\key.pem" -out "$SSL_DIR\cert.pem"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to generate certificate" -ForegroundColor Red
    exit 1
}

# Remove CSR file (no longer needed)
Remove-Item "$SSL_DIR\cert.csr" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "SSL Certificates Generated Successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Certificate: $SSL_DIR\cert.pem"
Write-Host "Private Key: $SSL_DIR\key.pem"
Write-Host ""
Write-Host "To use HTTPS:"
Write-Host "1. Set SSL_ENABLED=true in your .env file"
Write-Host "2. Start with SSL profile: docker-compose --profile ssl up -d"
Write-Host ""
Write-Host "IMPORTANT: For production, replace with certificates from"
Write-Host "a trusted Certificate Authority (Let's Encrypt, etc.)"
Write-Host "============================================================" -ForegroundColor Yellow
