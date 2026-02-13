# ==========================================
# CLEANUP SCRIPT FOR DEPLOYMENT
# Run this before pushing to GitHub
# ==========================================

Write-Host "🧹 Cleaning up unnecessary files for deployment..." -ForegroundColor Cyan
Write-Host ""

# Remove node_modules (HEAVY - 200MB+)
Write-Host "📦 Removing node_modules..." -ForegroundColor Yellow
if (Test-Path "website\krishna-react\node_modules") {
    Remove-Item -Path "website\krishna-react\node_modules" -Recurse -Force
    Write-Host "✅ Removed node_modules" -ForegroundColor Green
} else {
    Write-Host "⏭️  node_modules not found (already clean)" -ForegroundColor Gray
}

# Remove React build folder
Write-Host "📦 Removing React build folder..." -ForegroundColor Yellow
if (Test-Path "website\krishna-react\build") {
    Remove-Item -Path "website\krishna-react\build" -Recurse -Force
    Write-Host "✅ Removed build folder" -ForegroundColor Green
} else {
    Write-Host "⏭️  build folder not found (already clean)" -ForegroundColor Gray
}

# Remove Python cache
Write-Host "📦 Removing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Write-Host "✅ Removed __pycache__ folders" -ForegroundColor Green

# Remove virtual environment
Write-Host "📦 Removing virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Remove-Item -Path "venv" -Recurse -Force
    Write-Host "✅ Removed venv" -ForegroundColor Green
} else {
    Write-Host "⏭️  venv not found (already clean)" -ForegroundColor Gray
}

# Remove database (will be recreated on Render)
Write-Host "📦 Removing local database..." -ForegroundColor Yellow
if (Test-Path "users.db") {
    Remove-Item -Path "users.db" -Force
    Write-Host "✅ Removed users.db" -ForegroundColor Green
} else {
    Write-Host "⏭️  users.db not found (already clean)" -ForegroundColor Gray
}

if (Test-Path "website\users.db") {
    Remove-Item -Path "website\users.db" -Force
    Write-Host "✅ Removed website\users.db" -ForegroundColor Green
}

# Remove audio cache
Write-Host "📦 Removing audio cache..." -ForegroundColor Yellow
if (Test-Path "website\audio_cache") {
    Remove-Item -Path "website\audio_cache" -Recurse -Force
    Write-Host "✅ Removed audio_cache" -ForegroundColor Green
} else {
    Write-Host "⏭️  audio_cache not found (already clean)" -ForegroundColor Gray
}

# Remove .env files (keep .env.example)
Write-Host "📦 Removing .env files..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Remove-Item -Path ".env" -Force
    Write-Host "✅ Removed .env" -ForegroundColor Green
}
if (Test-Path "website\krishna-react\.env") {
    Remove-Item -Path "website\krishna-react\.env" -Force
    Write-Host "✅ Removed frontend .env" -ForegroundColor Green
}

# Remove npm cache
Write-Host "📦 Cleaning npm cache..." -ForegroundColor Yellow
if (Test-Path "website\krishna-react\node_modules\.cache") {
    Remove-Item -Path "website\krishna-react\node_modules\.cache" -Recurse -Force
    Write-Host "✅ Removed npm cache" -ForegroundColor Green
}

Write-Host ""
Write-Host "✨ Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 What was removed:" -ForegroundColor Cyan
Write-Host "  - node_modules/ (Frontend dependencies - ~200MB)" -ForegroundColor Gray
Write-Host "  - build/ (React build folder)" -ForegroundColor Gray
Write-Host "  - __pycache__/ (Python cache)" -ForegroundColor Gray
Write-Host "  - venv/ (Virtual environment)" -ForegroundColor Gray
Write-Host "  - users.db (Local database)" -ForegroundColor Gray
Write-Host "  - audio_cache/ (Generated audio files)" -ForegroundColor Gray
Write-Host "  - .env files (Environment variables)" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Your code is now clean and ready for deployment!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "  1. git add ." -ForegroundColor Yellow
Write-Host "  2. git commit -m 'Production ready'" -ForegroundColor Yellow
Write-Host "  3. git push" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Render and Vercel will install everything automatically!" -ForegroundColor Magenta
