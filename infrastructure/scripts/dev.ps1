<#
.SYNOPSIS
    Development helper script for PowerShell on Windows.
.DESCRIPTION
    Provides commands to manage Docker infrastructure, local backend, and frontend.
.EXAMPLE
    .\infrastructure\scripts\dev.ps1 infra-up
    .\infrastructure\scripts\dev.ps1 backend
    .\infrastructure\scripts\dev.ps1 frontend
#>

param (
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("infra-up", "infra-down", "up", "down", "ps", "logs", "backend", "frontend", "test", "help")]
    [string]$Action
)

$ComposeCmd = "docker-compose"
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    $ComposePath = "C:\Users\Sandip Sah\AppData\Local\Programs\DockerDesktop\resources\bin\docker-compose.exe"
    if (Test-Path $ComposePath) {
        $ComposeCmd = "& `"$ComposePath`""
    }
}

switch ($Action) {
    "infra-up" {
        Write-Host "Starting core infrastructure (PostgreSQL + pgvector, Redis, Ollama)..." -ForegroundColor Cyan
        Invoke-Expression "$ComposeCmd up -d postgres redis ollama"
    }
    "infra-down" {
        Write-Host "Stopping core infrastructure..." -ForegroundColor Yellow
        Invoke-Expression "$ComposeCmd stop postgres redis ollama"
    }
    "up" {
        Write-Host "Starting all services with Docker Compose..." -ForegroundColor Cyan
        Invoke-Expression "$ComposeCmd up -d --build"
    }
    "down" {
        Write-Host "Stopping all Docker services..." -ForegroundColor Yellow
        Invoke-Expression "$ComposeCmd down"
    }
    "ps" {
        Invoke-Expression "$ComposeCmd ps"
    }
    "logs" {
        Invoke-Expression "$ComposeCmd logs -f"
    }
    "backend" {
        Write-Host "Starting FastAPI backend locally..." -ForegroundColor Green
        Set-Location "$PSScriptRoot\..\..\backend"
        python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }
    "frontend" {
        Write-Host "Starting React + Vite frontend locally..." -ForegroundColor Green
        Set-Location "$PSScriptRoot\..\..\frontend"
        npm run dev
    }
    "test" {
        Write-Host "Running tests..." -ForegroundColor Cyan
        Set-Location "$PSScriptRoot\..\..\backend"
        python -m pytest
        Set-Location "$PSScriptRoot\..\..\frontend"
        npm run test
    }
    "help" {
        Write-Host "Available actions: infra-up, infra-down, up, down, ps, logs, backend, frontend, test" -ForegroundColor White
    }
}
