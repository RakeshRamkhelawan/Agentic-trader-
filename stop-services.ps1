# Agentic Trader Platform - Stop All Services

Write-Host "🛑 Stopping services..." -ForegroundColor Yellow

# Read PIDs if available
if (Test-Path ".service-pids") {
    $content = Get-Content ".service-pids"
    foreach ($line in $content) {
        if ($line -match "PID:\s*(\d+)") {
            $pid = $matches[1]
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "✅ Stopped process $pid" -ForegroundColor Green
            } catch {
                Write-Host "⚠️  Could not stop process $pid" -ForegroundColor Yellow
            }
        }
    }
    Remove-Item ".service-pids" -ErrorAction SilentlyContinue
}

# Kill any uvicorn processes in this directory
Get-Process -Name "python" -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "*$PWD*" } |
    ForEach-Object {
        Stop-Process -Id $_.Id -Force
        Write-Host "✅ Stopped Python process $($_.Id)" -ForegroundColor Green
    }

# Kill npm/node processes for this project
Get-Process -Name "node" -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "*$PWD*" } |
    ForEach-Object {
        Stop-Process -Id $_.Id -Force
        Write-Host "✅ Stopped Node process $($_.Id)" -ForegroundColor Green
    }

Write-Host ""
Write-Host "✅ All services stopped!" -ForegroundColor Green
