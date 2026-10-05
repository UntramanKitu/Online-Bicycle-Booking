@echo off
cd /d %~dp0
.venv\Scripts\uvicorn.exe app.main:app --reload --host localhost --port 8000
