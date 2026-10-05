@echo off
REM สตาร์ท frontend แบบหน้าต่างแยก — ปิด VS Code / terminal นี้แล้ว dev server ยังรันอยู่
cd /d "%~dp0frontend"
start "BikeA frontend :5173" npm run dev -- --host 127.0.0.1 --port 5173
echo Frontend started in a new window (http://127.0.0.1:5173)
pause
