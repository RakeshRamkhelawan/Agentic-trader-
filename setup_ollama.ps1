# Ollama Setup Script for Agentic Trader Platform
# Usage: .\setup_ollama.ps1 [model_name]

param(
    [string]$Model = "llama3.2"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Agentic Trader Platform - Ollama Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Model: $Model"
Write-Host ""

# Check if Ollama container is running
$ollamaRunning = docker-compose ps | Select-String "ollama.*Up"
if (-not $ollamaRunning) {
    Write-Host "Starting Ollama container..." -ForegroundColor Yellow
    docker-compose --profile llm up -d ollama
    Write-Host "Waiting for Ollama to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

Write-Host "Downloading model: $Model" -ForegroundColor Green
Write-Host "This may take several minutes depending on the model size..." -ForegroundColor Yellow
Write-Host ""

docker-compose exec ollama ollama pull $Model

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Model downloaded successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Testing model..." -ForegroundColor Yellow
docker-compose exec ollama ollama run $Model "Hello, are you working?"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Ollama is ready to use!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Update your .env file:" -ForegroundColor Cyan
Write-Host "  LLM_PROVIDER=ollama" -ForegroundColor White
Write-Host "  OLLAMA_BASE_URL=http://ollama:11434" -ForegroundColor White
Write-Host "  OLLAMA_MODEL=$Model" -ForegroundColor White
Write-Host ""
Write-Host "Available models:" -ForegroundColor Cyan
docker-compose exec ollama ollama list
Write-Host "============================================================" -ForegroundColor Cyan
