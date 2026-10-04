# ==============================================================================
# WealthGuard AI — Production Backup Script (PowerShell)
# Performs PostgreSQL database dump and archives persistent Docker volumes.
# ==============================================================================
$ErrorActionPreference = "Stop"

$BackupDir = If ($env:BACKUP_DIR) { $env:BACKUP_DIR } Else { ".\backups" }
$Timestamp = (Get-Date).ToString("yyyy-MM-dd_HHmmss")
$PostgresContainer = If ($env:POSTGRES_CONTAINER) { $env:POSTGRES_CONTAINER } Else { "gaa_postgres" }
$PostgresUser = If ($env:POSTGRES_USER) { $env:POSTGRES_USER } Else { "postgres" }
$PostgresDb = If ($env:POSTGRES_DB) { $env:POSTGRES_DB } Else { "gaa_db" }

If (!(Test-Path -Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$AbsBackupDir = (Resolve-Path $BackupDir).Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting WealthGuard AI Disaster Recovery Backup: $Timestamp" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. PostgreSQL Database Dump
Write-Host "[1/3] Dumping PostgreSQL database '$PostgresDb' from '$PostgresContainer'..." -ForegroundColor Yellow
$SqlFile = "$AbsBackupDir\backup_${PostgresDb}_${Timestamp}.sql"
docker exec -t $PostgresContainer pg_dump -U $PostgresUser $PostgresDb | Out-File -FilePath $SqlFile -Encoding utf8
Write-Host "      Saved to: $SqlFile" -ForegroundColor Green

# 2. Archive Uploaded Documents Volume
Write-Host "[2/3] Archiving uploads volume (gaa_backend_uploads)..." -ForegroundColor Yellow
docker run --rm -v gaa_backend_uploads:/data:ro -v "${AbsBackupDir}:/backup" alpine tar czf "/backup/uploads_${Timestamp}.tar.gz" -C /data .
Write-Host "      Saved to: $AbsBackupDir\uploads_${Timestamp}.tar.gz" -ForegroundColor Green

# 3. Archive ChromaDB Persistent Vector Storage
Write-Host "[3/3] Archiving ChromaDB vector storage volume (gaa_backend_chroma)..." -ForegroundColor Yellow
docker run --rm -v gaa_backend_chroma:/data:ro -v "${AbsBackupDir}:/backup" alpine tar czf "/backup/chroma_${Timestamp}.tar.gz" -C /data .
Write-Host "      Saved to: $AbsBackupDir\chroma_${Timestamp}.tar.gz" -ForegroundColor Green

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Backup completed successfully!" -ForegroundColor Cyan
Write-Host " Backups stored in: $AbsBackupDir" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
