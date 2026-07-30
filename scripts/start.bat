@echo off
cd /d "%~dp0\..\app\backend"
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)
set MES_DEV=1
start "LocalMES API" .venv\Scripts\uvicorn.exe main:app --reload --port 8000
cd ..\frontend
if not exist node_modules npm install
start "LocalMES UI" npm run dev
echo LocalMES starting: UI http://localhost:3000  API http://localhost:8000/docs
