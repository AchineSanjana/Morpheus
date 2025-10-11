@echo off
echo 🚀 Starting Morpheus Sleep AI - Backend Server
echo ===============================================

cd /d "C:\Users\admin\Desktop\sliit_work\Y3S1_DS\IRWA\Sleep improvemnt ai\Morpheus\backend"

echo 📁 Current directory: %CD%
echo 🐍 Starting Python backend server...

rem Activate venv if present
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python start_backend.py

if errorlevel 1 (
    echo ❌ Failed to start backend
    echo 💡 Make sure Python and dependencies are installed
    echo 💡 Try: pip install fastapi uvicorn python-dotenv
    pause
    exit /b 1
)

pause