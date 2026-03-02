# Monitor Training Progress
# Usage: .\scripts\monitor_training.ps1

Write-Host "📊 CHITTA TRAINING MONITOR" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

# Find training processes
$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*train_chitta*"
}

if ($processes) {
    Write-Host "✅ Training is RUNNING" -ForegroundColor Green
    $processes | ForEach-Object {
        Write-Host "   PID: $($_.Id) | CPU: $([math]::Round($_.CPU, 1))s | RAM: $([math]::Round($_.WorkingSet64 / 1MB, 0)) MB"
    }
} else {
    Write-Host "⚠️  Geen actieve training gevonden" -ForegroundColor Yellow
}

Write-Host ""

# Find latest log
$logFile = Get-ChildItem "models/production" -Filter "training_*.log" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($logFile) {
    Write-Host "📁 Log file: $($logFile.Name)" -ForegroundColor Cyan
    Write-Host "🕐 Last update: $($logFile.LastWriteTime)"
    Write-Host ""

    # Show progress
    $content = Get-Content $logFile.FullName -ErrorAction SilentlyContinue

    if ($content) {
        # Find epoch progress
        $epochLines = $content | Select-String "Epoch"
        if ($epochLines) {
            Write-Host "📈 Progress:" -ForegroundColor Green
            $epochLines | Select-Object -Last 5 | ForEach-Object {
                Write-Host "   $_"
            }
        }

        # Find errors
        $errorLines = $content | Select-String "Error|ERROR|Exception"
        if ($errorLines) {
            Write-Host ""
            Write-Host "⚠️  ERRORS GEVONDEN:" -ForegroundColor Red
            $errorLines | Select-Object -Last 3 | ForEach-Object {
                Write-Host "   $_" -ForegroundColor Red
            }
        }

        # Check if completed
        if ($content | Select-String "COMPLETE|completed successfully") {
            Write-Host ""
            Write-Host "🎉 TRAINING COMPLETED!" -ForegroundColor Green

            # Find model file
            $modelFile = Get-ChildItem "models/production" -Filter "chitta_*.pt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($modelFile) {
                Write-Host "   Model: $($modelFile.Name)" -ForegroundColor Green
                Write-Host "   Size: $([math]::Round($modelFile.Length / 1MB, 2)) MB" -ForegroundColor Green

                # Show metrics if available
                $historyFile = Get-ChildItem "models/production" -Filter "chitta_*_history.json" | Select-Object -First 1
                if ($historyFile) {
                    $history = Get-Content $historyFile | ConvertFrom-Json
                    $lastAcc = $history.val_acc[-1]
                    Write-Host "   Final Accuracy: $([math]::Round($lastAcc * 100, 1))%" -ForegroundColor Green
                }
            }
        }
    } else {
        Write-Host "⏳ Log is leeg - training is net gestart" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "🔍 Live monitoring:" -ForegroundColor Cyan
    Write-Host "   Get-Content '$($logFile.FullName)' -Tail 10 -Wait"
} else {
    Write-Host "❌ Geen log files gevonden in models/production/" -ForegroundColor Red
}

Write-Host ""
Write-Host "💡 Commands:" -ForegroundColor Cyan
Write-Host "   Stop training:     Get-Process python | Where-Object {`$_.CommandLine -like '*train_chitta*'} | Stop-Process"
Write-Host "   Force stop:        taskkill /F /IM python.exe"
Write-Host "   Bekijk alle logs:  Get-Content '$($logFile.FullName)'"
