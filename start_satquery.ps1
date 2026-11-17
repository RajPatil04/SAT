# SatQuery AI - PowerShell Full Platform Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "         Starting SatQuery AI Full Platform             " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

Write-Host "[1/4] Starting ChangeStar Microservice on port 8001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; `$env:PYTHONPATH='$root'; python -m uvicorn model_services.changestar_server:app --host 127.0.0.1 --port 8001"

Write-Host "[2/4] Starting CROMA Microservice on port 8002..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; `$env:PYTHONPATH='$root'; python -m uvicorn model_services.croma_server:app --host 127.0.0.1 --port 8002"

Write-Host "[3/4] Starting SatQuery Backend Gateway on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; `$env:PYTHONPATH='$root'; python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

Write-Host "[4/4] Starting React Frontend UI on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev -- --host 127.0.0.1"

Write-Host ""
Write-Host "All 4 SatQuery AI services are running:" -ForegroundColor Green
Write-Host "  * Mission Control Frontend : http://127.0.0.1:3000" -ForegroundColor White
Write-Host "  * Backend API Swagger Docs : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  * ChangeStar Microservice  : http://127.0.0.1:8001/health" -ForegroundColor White
Write-Host "  * CROMA Foundation Service : http://127.0.0.1:8002/health" -ForegroundColor White
Write-Host ""
