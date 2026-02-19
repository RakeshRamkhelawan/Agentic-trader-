# =============================================================================
# PRODUCTION DEPLOYMENT VALIDATION SCRIPT (PowerShell)
# Validates .env.prod and docker-compose.prod.yml before deployment
# =============================================================================

param(
    [string]$ComposeFile = "docker-compose.prod.yml",
    [string]$EnvFile = ".env.prod"
)

function Log-Info($message) {
    Write-Host -ForegroundColor Cyan "[INFO] $message"
}

function Log-Success($message) {
    Write-Host -ForegroundColor Green "[OK] $message"
}

function Log-Warning($message) {
    Write-Host -ForegroundColor Yellow "[WARN] $message"
}

function Log-Error($message) {
    Write-Host -ForegroundColor Red "[ERROR] $message"
}

# -----------------------------------------------------------------------------
# CHECK 1: .env.prod file exists
# -----------------------------------------------------------------------------
function Check-EnvFile {
    Log-Info "Checking .env.prod file..."
    
    if (-not (Test-Path $EnvFile)) {
        Log-Error ".env.prod file not found!"
        Log-Info "Copy .env.prod.example to .env.prod and configure it:"
        Log-Info "  Copy-Item .env.prod.example .env.prod"
        exit 1
    }
    
    Log-Success ".env.prod file exists"
}

# -----------------------------------------------------------------------------
# CHECK 2: Required variables are set
# -----------------------------------------------------------------------------
function Check-RequiredVars {
    Log-Info "Checking required environment variables..."
    
    $requiredVars = @(
        "DB_PASSWORD",
        "CLICKHOUSE_PASSWORD",
        "GRAFANA_ADMIN_PASSWORD",
        "JWT_SECRET_KEY"
    )
    
    $missing = 0
    $envContent = Get-Content $EnvFile -Raw
    
    foreach ($var in $requiredVars) {
        # Check if variable exists and is not a placeholder
        # Use (?m) for multiline regex to match start of each line
        $pattern = "(?m)^\s*$var\s*="
        $changeMePattern = "(?m)^\s*$var\s*=\s*CHANGE_ME"
        
        $hasVar = $envContent -match $pattern
        $isPlaceholder = $envContent -match $changeMePattern
        
        if (-not $hasVar -or $isPlaceholder) {
            Log-Error "Missing or not configured: $var"
            $missing = 1
        }
    }
    
    if ($missing -eq 1) {
        Log-Error "Some required variables are not configured!"
        exit 1
    }
    
    Log-Success "All required variables are configured"
}

# -----------------------------------------------------------------------------
# CHECK 3: No default/weak passwords
# -----------------------------------------------------------------------------
function Check-PasswordStrength {
    Log-Info "Checking password strength..."
    
    $weakPatterns = @("password", "123", "admin", "test", "change_me", "default")
    $weakFound = 0
    $envContent = Get-Content $EnvFile -Raw
    
    foreach ($pattern in $weakPatterns) {
        if ($envContent -match $pattern) {
            Log-Warning "Potential weak password detected containing: $pattern"
            $weakFound = 1
        }
    }
    
    if ($weakFound -eq 1) {
        Log-Warning "Consider using stronger passwords"
    } else {
        Log-Success "No obvious weak passwords detected"
    }
}

# -----------------------------------------------------------------------------
# CHECK 4: Docker Compose syntax validation
# -----------------------------------------------------------------------------
function Check-ComposeSyntax {
    Log-Info "Validating Docker Compose syntax..."
    
    try {
        $null = docker compose -f $ComposeFile --env-file $EnvFile config 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Validation failed"
        }
        Log-Success "Docker Compose syntax is valid"
    } catch {
        Log-Error "Docker Compose syntax validation failed!"
        Log-Info "Run the following to see details:"
        Log-Info "  docker compose -f $ComposeFile --env-file $EnvFile config"
        exit 1
    }
}

# -----------------------------------------------------------------------------
# CHECK 5: Environment variable substitution
# -----------------------------------------------------------------------------
function Check-EnvSubstitution {
    Log-Info "Checking environment variable substitution..."
    
    try {
        $null = docker compose -f $ComposeFile --env-file $EnvFile config 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Substitution failed"
        }
        Log-Success "Environment variable substitution successful"
    } catch {
        Log-Error "Environment variable substitution failed!"
        Log-Info "Check that all referenced variables are defined in $EnvFile"
        exit 1
    }
}

# -----------------------------------------------------------------------------
# CHECK 6: No localhost in production URLs (where inappropriate)
# -----------------------------------------------------------------------------
function Check-NoLocalhost {
    Log-Info "Checking for localhost references in production config..."
    
    $envContent = Get-Content $EnvFile -Raw
    $localhostPattern = "(DATABASE_URL|REDIS_URL|KAFKA).*localhost"
    
    if ($envContent -match $localhostPattern) {
        Log-Warning "Found localhost references in infrastructure URLs"
        Log-Warning "In Docker Compose, use service names (postgres, redis, redpanda) instead of localhost"
    } else {
        Log-Success "No localhost references in infrastructure URLs"
    }
}

# -----------------------------------------------------------------------------
# CHECK 7: ENV=production
# -----------------------------------------------------------------------------
function Check-ProductionEnv {
    Log-Info "Checking ENV setting..."
    
    $envContent = Get-Content $EnvFile -Raw
    if ($envContent -match 'ENV=production') {
        Log-Success "ENV is set to production"
    } else {
        Log-Warning "ENV is not set to production"
        Log-Info "Add to $EnvFile`: ENV=production"
    }
}

# -----------------------------------------------------------------------------
# CHECK 8: DEBUG=False
# -----------------------------------------------------------------------------
function Check-DebugDisabled {
    Log-Info "Checking DEBUG setting..."
    
    $envContent = Get-Content $EnvFile -Raw
    if ($envContent -match 'DEBUG=False') {
        Log-Success "DEBUG is disabled"
    } else {
        Log-Warning "DEBUG may be enabled in production"
        Log-Info "Add to $EnvFile`: DEBUG=False"
    }
}

# -----------------------------------------------------------------------------
# CHECK 9: .env.prod is in .gitignore
# -----------------------------------------------------------------------------
function Check-Gitignore {
    Log-Info "Checking .gitignore..."
    
    if (Test-Path ".gitignore") {
        $gitignore = Get-Content ".gitignore" -Raw
        if ($gitignore -match "\.env\.prod") {
            Log-Success ".env.prod is in .gitignore"
        } else {
            Log-Error ".env.prod is NOT in .gitignore!"
            Log-Info "Add the following to .gitignore:"
            Log-Info "  .env.prod"
            exit 1
        }
    } else {
        Log-Warning ".gitignore file not found"
    }
}

# -----------------------------------------------------------------------------
# CHECK 10: Required files exist
# -----------------------------------------------------------------------------
function Check-RequiredFiles {
    Log-Info "Checking required files..."
    
    $requiredFiles = @(
        "infrastructure/docker/Dockerfile.backend",
        "infrastructure/docker/Dockerfile.frontend.prod"
    )
    
    $missing = 0
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Log-Error "Required file not found: $file"
            $missing = 1
        }
    }
    
    if ($missing -eq 1) {
        exit 1
    }
    
    Log-Success "All required files exist"
}

# -----------------------------------------------------------------------------
# PRINT CONFIGURATION SUMMARY
# -----------------------------------------------------------------------------
function Print-Summary {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  PRODUCTION CONFIGURATION SUMMARY"
    Write-Host "========================================"
    Write-Host ""
    
    # Count services
    $services = docker compose -f $ComposeFile --env-file $EnvFile config --services 2>$null
    $serviceCount = ($services | Measure-Object).Count
    Write-Host "Services to deploy: $serviceCount"
    
    # Show images
    Write-Host ""
    Write-Host "Images:"
    $config = docker compose -f $ComposeFile --env-file $EnvFile config 2>$null
    $images = $config | Select-String "image:" | ForEach-Object { $_ -replace '.*image: ', '  - ' }
    $images
    
    # Show exposed ports
    Write-Host ""
    Write-Host "Exposed ports:"
    $ports = $config | Select-String "published:" | ForEach-Object { $_ -replace '.*published: ', '  - ' }
    if ($ports) { $ports } else { Write-Host "  (See docker-compose.prod.yml for port mappings)" }
    
    Write-Host ""
    Write-Host "========================================"
}

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
function Main {
    Write-Host "========================================"
    Write-Host "  PRODUCTION DEPLOYMENT VALIDATION"
    Write-Host "========================================"
    Write-Host ""
    
    Check-EnvFile
    Check-RequiredVars
    Check-PasswordStrength
    Check-Gitignore
    Check-ComposeSyntax
    Check-EnvSubstitution
    Check-NoLocalhost
    Check-ProductionEnv
    Check-DebugDisabled
    Check-RequiredFiles
    
    Write-Host ""
    Log-Success "All validation checks passed!"
    Write-Host ""
    
    Print-Summary
    
    Write-Host ""
    Write-Host "To deploy, run:"
    Write-Host "  docker compose -f $ComposeFile --env-file $EnvFile up -d"
    Write-Host ""
}

Main
