# PowerShell script to start 8-hour paper trading session
# This runs in the background and logs to a file

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "paper_trading_8h_$timestamp.log"

Write-Host "Starting 8-hour Ultimate Paper Trading Session"
Write-Host "Log file: $logFile"
Write-Host ""
Write-Host "Session Details:"
Write-Host "  - Duration: 8 hours"
Write-Host "  - Capital: EUR 10,000"
Write-Host "  - Exchanges: Bitvavo + Revolut X"
Write-Host "  - Symbols: All available pairs"
Write-Host ""
Write-Host "Press Ctrl+C to stop (or let it run for 8 hours)"
Write-Host ""

# Start the trading session
python scripts/ultimate_paper_trading.py --duration 8 --capital 10000 2>&1 | Tee-Object -FilePath $logFile

Write-Host ""
Write-Host "Session complete! Check $logFile for details"
