# Startup Script for SQL Optimizer App
Write-Host "Starting SQL Optimizer..." -ForegroundColor Cyan

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py" -WorkingDirectory "$PSScriptRoot"
Write-Host "Backend started in new window." -ForegroundColor Green

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -WorkingDirectory "$PSScriptRoot"
Write-Host "Frontend started in new window." -ForegroundColor Green

Write-Host "App is launching! Check the new windows." -ForegroundColor Yellow
