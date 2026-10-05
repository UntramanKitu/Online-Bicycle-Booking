@echo off
REM BikeA - start backend + frontend แบบหน้าต่างแยก (ปิด VS Code แล้ว server ยังรันต่อ)
cd /d "%~dp0backend"
start "BikeA backend :8002" cmd /c "uv run uvicorn app.main:app --host 127.0.0.1 --port 8002"
cd /d "%~dp0frontend"
start "BikeA frontend :5173" cmd /c "npm run dev -- --host 127.0.0.1 --port 5173"
echo Started backend (http://127.0.0.1:8002) + frontend (http://127.0.0.1:5173)
echo Login: http://127.0.0.1:5173/login
pause
