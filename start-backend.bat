@echo off
REM สตาร์ท backend แบบหน้าต่างแยก — ปิด VS Code / terminal นี้แล้ว server ยังรันอยู่
cd /d "%~dp0backend"
start "BikeA backend :8002" uv run uvicorn app.main:app --host 127.0.0.1 --port 8002
echo Backend started in a new window (http://127.0.0.1:8002)
pause
