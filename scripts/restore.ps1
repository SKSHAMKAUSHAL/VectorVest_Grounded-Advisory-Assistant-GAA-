# ==============================================================================
# WealthGuard AI — Production Restore Script (PowerShell)
# Usage: .\scripts\restore.ps1 -SqlFile path\to\backup.sql -UploadsTar path\to\uploads.tar.gz -ChromaTar path\to\chroma.tar.gz
# ==============================================================================
param(
    [Parameter(Mandatory=$true)]
    [string]$SqlFile,

    [Parameter(Mandatory=$true)]
    [string]$UploadsTar,

    [Parameter(Mandatory=$true)]
    [string]$ChromaTar
)

$ErrorActionPreference = "Stop"

$PostgresContainer = If ($env:POSTGRES_CONTAINER) { $env:POSTGRES_CONTAINER } Else { "gaa_postgres" }
$PostgresUser = If ($env:POSTGRES_USER) { $env:POSTGRES_USER } Else { "postgres" }
$PostgresDb = If ($env:POSTGRES_DB) { $env:POSTGRES_DB } Else { "gaa_db" }

$AbsSqlFile = (Resolve-Path $SqlFile).Path
$AbsUploadsTar = (Resolve-Path $UploadsTar).Path
$AbsChromaTar = (Resolve-Path $ChromaTar).Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting WealthGuard AI Disaster Recovery Restore" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Restore PostgreSQL Database
Write-Host "[1/3] Restoring PostgreSQL database from $AbsSqlFile..." -ForegroundColor Yellow
Get-Content -Path $AbsSqlFile | docker exec -i $PostgresContainer psql -U $PostgresUser -d $PostgresDb
Write-Host "      Database restored." -ForegroundColor Green

# 2. Restore Uploads Volume
Write-Host "[2/3] Restoring uploads volume from $AbsUploadsTar..." -ForegroundColor Yellow
$UploadsDir = Split-Path -Parent $AbsUploadsTar
$UploadsFileName = Split-Path -Leaf $AbsUploadsTar
docker run --rm -v gaa_backend_uploads:/data -v "${UploadsDir}:/backup" alpine sh -c "rm -rf /data/* && tar xzf /backup/$UploadsFileName -C /data"
Write-Host "      Uploads restored." -ForegroundColor Green

# 3. Restore ChromaDB Vector Storage
Write-Host "[3/3] Restoring ChromaDB storage from $AbsChromaTar..." -ForegroundColor Yellow
$ChromaDir = Split-Path -Parent $AbsChromaTar
$ChromaFileName = Split-Path -Leaf $AbsChromaTar
docker run --rm -v gaa_backend_chroma:/data -v "${ChromaDir}:/backup" alpine sh -c "rm -rf /data/* && tar xzf /backup/$ChromaFileName -C /data"
Write-Host "      ChromaDB restored." -ForegroundColor Green

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Restore completed successfully!" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
