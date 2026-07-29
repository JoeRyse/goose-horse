# Auto-update and Push New Track Cards to GitHub & Vercel
$ErrorActionPreference = "Stop"

$env:PATH = "C:\Users\joery\.node-bin;" + $env:PATH
$workspace = $PSScriptRoot

Write-Host "=========================================" -ForegroundColor Gold
Write-Host "  EXACTA AI - AUTO UPDATE & GITHUB PUSH  " -ForegroundColor Gold
Write-Host "=========================================" -ForegroundColor Gold

# 1. Export static JSON cards
Write-Host "`n[1/3] Refreshing static track card data..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File "$workspace\scratch\export_static.ps1"

# 2. Build production bundle
Write-Host "`n[2/3] Building production web app..." -ForegroundColor Cyan
Set-Location "$workspace\frontend"
npm run build

# 3. Commit and push to GitHub
Write-Host "`n[3/3] Pushing updates to GitHub (JoeRyse/goose-horse)..." -ForegroundColor Cyan
Set-Location $workspace
git add .
git commit -m "update: Add new race cards ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
git push origin main

Write-Host "`n✅ SUCCESS! New track cards pushed to GitHub." -ForegroundColor Green
Write-Host "🚀 Vercel will automatically update your live web app in ~30 seconds!" -ForegroundColor Green
