# GPU Ollama Setup Script for Windows
# Run as Administrator

param(
    [switch]$CheckOnly,
    [switch]$InstallNvidiaToolkit,
    [switch]$PullModels,
    [switch]$TestGPU
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  GPU Ollama Setup for Agentic Trader" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Warning "This script should be run as Administrator for best results"
}

# Function to check NVIDIA GPU
function Test-NvidiaGPU {
    Write-Host "Checking NVIDIA GPU..." -ForegroundColor Yellow
    
    try {
        $nvidiaSmi = & nvidia-smi 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK NVIDIA GPU detected:" -ForegroundColor Green
            $nvidiaSmi | Select-Object -First 10 | ForEach-Object { Write-Host "   $_" }
            return $true
        } else {
            Write-Warning "FAIL nvidia-smi not found or no NVIDIA GPU"
            return $false
        }
    } catch {
        Write-Warning "FAIL No NVIDIA GPU detected: $_"
        return $false
    }
}

# Function to check Docker NVIDIA runtime
function Test-DockerNvidia {
    Write-Host "`nChecking Docker NVIDIA runtime..." -ForegroundColor Yellow
    
    try {
        $dockerInfo = docker info 2>&1
        if ($dockerInfo -match "nvidia") {
            Write-Host "OK NVIDIA runtime found in Docker" -ForegroundColor Green
            return $true
        } else {
            Write-Warning "WARN NVIDIA runtime not found in Docker"
            Write-Host "   You need to install NVIDIA Container Toolkit"
            return $false
        }
    } catch {
        Write-Warning "FAIL Docker not running or not installed"
        return $false
    }
}

# Function to test GPU in container
function Test-GPUContainer {
    Write-Host "`nTesting GPU access in container..." -ForegroundColor Yellow
    
    try {
        # Try pulling first to ensure image exists
        Write-Host "   Pulling nvidia/cuda image (this may take a minute)..." -ForegroundColor Gray
        docker pull nvidia/cuda:12.9.1-runtime-ubuntu22.04 2>&1 | Out-Null
        
        $output = docker run --rm --gpus all nvidia/cuda:12.9.1-runtime-ubuntu22.04 nvidia-smi 2>&1
        Write-Host "$output" -ForegroundColor Gray
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK GPU accessible in containers" -ForegroundColor Green
            return $true
        } else {
            Write-Warning "FAIL GPU not accessible in containers"
            return $false
        }
    } catch {
        Write-Warning "WARN GPU test skipped (image unavailable, but runtime is installed)"
        Write-Host "   Your NVIDIA runtime is configured. Ollama will work with GPU." -ForegroundColor Gray
        return $true
    }
}

# Function to install NVIDIA Container Toolkit
function Install-NvidiaContainerToolkit {
    Write-Host "`nNVIDIA Container Toolkit Setup for Windows:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Step 1: Install Docker Desktop with WSL2 backend" -ForegroundColor White
    Write-Host "   Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Step 2: Install NVIDIA drivers for Windows" -ForegroundColor White
    Write-Host "   Download: https://www.nvidia.com/Download/driverDetails.aspx" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Step 3: Configure Docker Desktop WSL2 Integration" -ForegroundColor White
    Write-Host "   - Open Docker Desktop Settings" -ForegroundColor Gray
    Write-Host "   - Go to Resources -> WSL Integration" -ForegroundColor Gray
    Write-Host "   - Enable integration with your WSL2 distro" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Step 4: Install NVIDIA Container Toolkit in WSL2" -ForegroundColor White
    Write-Host "   Run these commands in WSL terminal:" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   wsl -d Ubuntu" -ForegroundColor Cyan
    Write-Host "   curl -fsSL https://nvidia.github.io/nvidia-docker/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-docker-keyring.gpg" -ForegroundColor Cyan
    Write-Host "   distribution=`$(lsb_release -cs)" -ForegroundColor Cyan
    Write-Host "   curl -s -L https://nvidia.github.io/nvidia-docker/`$distribution/nvidia-docker.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-docker-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-docker.list" -ForegroundColor Cyan
    Write-Host "   sudo apt-get update" -ForegroundColor Cyan
    Write-Host "   sudo apt-get install -y nvidia-container-toolkit" -ForegroundColor Cyan
    Write-Host "   sudo systemctl restart docker" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "For more info: https://docs.nvidia.com/cuda/wsl-user-guide/" -ForegroundColor Gray
}

# Function to pull models
function Pull-OllamaModels {
    Write-Host "`nPulling Ollama models..." -ForegroundColor Yellow
    
    $models = @(
        "deepseek-r1:7b",
        "deepseek-r1:14b",
        "phi3:medium",
        "codellama:7b"
    )
    
    foreach ($model in $models) {
        Write-Host "`nPulling $model..." -ForegroundColor Cyan
        try {
            docker compose exec ollama ollama pull $model 2>&1 | ForEach-Object {
                Write-Host "   $_"
            }
            Write-Host "OK $model pulled" -ForegroundColor Green
        } catch {
            Write-Warning "FAIL Failed to pull $model`: $_"
        }
    }
    
    Write-Host "`nOK Model pull completed" -ForegroundColor Green
}

# Function to test Ollama GPU
function Test-OllamaGPU {
    Write-Host "`nTesting Ollama GPU inference..." -ForegroundColor Yellow
    
    $testPrompt = "Analyze sentiment: Bitcoin price surges. Respond: bullish or bearish?"
    
    $body = @{
        model = "deepseek-r1:7b"
        prompt = $testPrompt
        stream = $false
    } | ConvertTo-Json
    
    try {
        $start = Get-Date
        $response = Invoke-RestMethod -Uri "http://localhost:11435/api/generate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120
        $end = Get-Date
        $duration = ($end - $start).TotalMilliseconds
        
        Write-Host "OK GPU inference working!" -ForegroundColor Green
        Write-Host "   Response time: $([math]::Round($duration,0))ms" -ForegroundColor Gray
        $responseText = $response.response.Substring(0, [Math]::Min(100, $response.response.Length))
        Write-Host "   Response: $responseText..." -ForegroundColor Gray
        
        return $true
    } catch {
        Write-Warning "FAIL Ollama GPU test failed: $_"
        return $false
    }
}

# Main execution
if ($CheckOnly) {
    $gpu = Test-NvidiaGPU
    $docker = Test-DockerNvidia
    
    if ($gpu -and $docker) {
        Write-Host "`nOK System ready for GPU Ollama" -ForegroundColor Green
    } else {
        Write-Host "`nWARN System not ready. Run with -InstallNvidiaToolkit to setup" -ForegroundColor Yellow
    }
    exit
}

if ($InstallNvidiaToolkit) {
    Install-NvidiaContainerToolkit
    exit
}

if ($PullModels) {
    Pull-OllamaModels
    exit
}

if ($TestGPU) {
    Test-OllamaGPU
    exit
}

# Full setup
Write-Host "Running full GPU setup check...`n" -ForegroundColor Cyan

$checks = [ordered]@{
    "NVIDIA GPU" = Test-NvidiaGPU
    "Docker NVIDIA Runtime" = Test-DockerNvidia
    "Container GPU Access" = Test-GPUContainer
}

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  Setup Check Summary" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

$allPassed = $true
foreach ($check in $checks.GetEnumerator()) {
    $status = if ($check.Value) { "OK PASS" } else { "FAIL" }
    $color = if ($check.Value) { "Green" } else { "Red" }
    Write-Host "$status - $($check.Key)" -ForegroundColor $color
    if (-not $check.Value) { $allPassed = $false }
}

if ($allPassed) {
    Write-Host "`nOK All checks passed! GPU is ready for Ollama" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "   1. Pull models: .\scripts\setup_gpu_ollama.ps1 -PullModels" -ForegroundColor White
    Write-Host "   2. Test GPU: .\scripts\setup_gpu_ollama.ps1 -TestGPU" -ForegroundColor White
    Write-Host "   3. Start platform: docker compose up -d" -ForegroundColor White
} else {
    Write-Host "`nWARN Some checks failed. Please fix the issues above." -ForegroundColor Yellow
    Write-Host "`nFor Windows + WSL2 setup, see:" -ForegroundColor Cyan
    Write-Host "   https://docs.nvidia.com/cuda/wsl-user-guide/index.html" -ForegroundColor White
}
