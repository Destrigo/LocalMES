@echo off
REM LocalMES — one-click production start for shop PCs (no coding required)
cd /d "%~dp0\.."

where python >nul 2>&1
if errorlevel 1 (
  echo Python non trovato. Installa Python 3.10+ da python.org e riprova.
  pause
  exit /b 1
)
where node >nul 2>&1
if errorlevel 1 (
  echo Node.js non trovato. Installa Node 18+ da nodejs.org e riprova.
  pause
  exit /b 1
)

cd app\backend
if not exist .venv (
  echo Creo ambiente Python...
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)

cd ..\frontend
if not exist node_modules (
  echo Installo dipendenze frontend...
  call npm install
)
echo Build frontend...
call npm run build
if errorlevel 1 (
  echo Build fallita.
  pause
  exit /b 1
)

cd ..\backend
set MES_DEV=0
if "%MES_SECRET_KEY%"=="" set MES_SECRET_KEY=localmes-change-me-please
echo.
echo LocalMES in produzione su http://localhost:8000
echo Apri questo indirizzo dal browser (anche da altri PC in rete: http://NOME-PC:8000)
echo.
.venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
pause
