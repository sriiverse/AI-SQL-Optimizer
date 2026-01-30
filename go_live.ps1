# Launch the App components first
Write-Host "Launching Backend and Frontend..." -ForegroundColor Cyan
. "$PSScriptRoot\start_app.ps1"

Write-Host "Waiting 10 seconds for servers to fully initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Launch LocalTunnel with QR Code
Write-Host "Starting Public Tunnel..." -ForegroundColor Magenta
Write-Host "Installing dependencies (first run only)..." -ForegroundColor Gray

# We use npx to run the script without polluting global node_modules, 
# but we need localtunnel and qrcode-terminal available. 
# Simplest way for a standalone script is to just install them in a temp way or assume they are there.
# Let's try running with npx dependencies explicitly or simple npm i in the root if needed.
# Better yet, let's just use npm install in the root for these tool deps to ensure they persist.

if (!(Test-Path "$PSScriptRoot\node_modules\localtunnel")) {
    Write-Host "Installing tunnel dependencies..." -ForegroundColor Yellow
    cmd /c "npm install localtunnel qrcode-terminal --no-save"
}

# Run the node script
Start-Process powershell -ArgumentList "-NoExit", "-Command", "node tunnel.js" -WorkingDirectory "$PSScriptRoot"

Write-Host "Tunnel window launched!" -ForegroundColor Green
Write-Host "Check the new window for your QR Code." -ForegroundColor Gray
