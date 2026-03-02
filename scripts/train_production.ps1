# Production Training Script for Windows
# Usage: .\scripts\train_production.ps1

Write-Host "========================================" -ForegroundColor Green
Write-Host "CHITTA PRODUCTION TRAINING" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Started at: $(Get-Date)"
Write-Host ""

# Config
$MODEL_TYPE = "transformer"
$EPOCHS = 50
$HIDDEN_SIZE = 256
$NUM_LAYERS = 4
$BATCH_SIZE = 32
$OUTPUT_DIR = "models/production"

# Create output dir
New-Item -ItemType Directory -Force -Path $OUTPUT_DIR | Out-Null

# Log file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LOG_FILE = "$OUTPUT_DIR/training_$timestamp.log"

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Model: $MODEL_TYPE"
Write-Host "  Epochs: $EPOCHS"
Write-Host "  Hidden size: $HIDDEN_SIZE"
Write-Host "  Layers: $NUM_LAYERS"
Write-Host "  Batch size: $BATCH_SIZE"
Write-Host "  Log: $LOG_FILE"
Write-Host ""

Write-Host "Starting training..." -ForegroundColor Yellow
Write-Host "Dit duurt 2-4 uur. Je kunt dit venster sluiten, training loopt door." -ForegroundColor Yellow
Write-Host ""

# Start training in background job
$job = Start-Job -ScriptBlock {
    param($MODEL_TYPE, $EPOCHS, $HIDDEN_SIZE, $NUM_LAYERS, $BATCH_SIZE, $OUTPUT_DIR, $LOG_FILE)

    python scripts/train_chitta_ultimate.py `
        --model-type $MODEL_TYPE `
        --epochs $EPOCHS `
        --hidden-size $HIDDEN_SIZE `
        --num-layers $NUM_LAYERS `
        --batch-size $BATCH_SIZE `
        --output-dir $OUTPUT_DIR `
        --save-history `
        > $LOG_FILE 2>&1

} -ArgumentList $MODEL_TYPE, $EPOCHS, $HIDDEN_SIZE, $NUM_LAYERS, $BATCH_SIZE, $OUTPUT_DIR, $LOG_FILE

# Save job info
$job.Id | Out-File "$OUTPUT_DIR/training_job_id.txt"

Write-Host "Training started with Job ID: $($job.Id)" -ForegroundColor Green
Write-Host ""
Write-Host "To monitor progress:" -ForegroundColor Cyan
Write-Host "  Get-Job -Id $($job.Id)"
Write-Host "  Receive-Job -Id $($job.Id) -Keep"
Write-Host "  tail -Path $LOG_FILE -Wait  (of: Get-Content $LOG_FILE -Tail 10 -Wait)"
Write-Host ""
Write-Host "To stop training:" -ForegroundColor Red
Write-Host "  Stop-Job -Id $($job.Id)"
Write-Host "  Remove-Job -Id $($job.Id)"
Write-Host ""
Write-Host "Model wordt opgeslagen in: $OUTPUT_DIR/" -ForegroundColor Green
Write-Host ""

# Optioneel: toon direct de logs
Write-Host "Monitoring logs (Ctrl+C om te stoppen met kijken, training loopt door):" -ForegroundColor Yellow
Start-Sleep -Seconds 2
Get-Content $LOG_FILE -Wait
