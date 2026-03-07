# =============================================================================
# Run Database Migrations (PowerShell)
# =============================================================================

Write-Host "🔄 Running database migrations..." -ForegroundColor Cyan

# Change to project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptDir "..")

# Run migrations using alembic
try {
    python -m alembic upgrade head
    Write-Host "✅ Migrations complete!" -ForegroundColor Green
} catch {
    Write-Host "❌ Migration failed: $_" -ForegroundColor Red
    exit 1
}
