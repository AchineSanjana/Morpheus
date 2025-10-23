@echo off
echo 🚀 Starting Morpheus Sleep AI Frontend
echo ========================================

cd /d "C:\Users\sanjana\Projects\Morpheus\frontend"

echo 📁 Current directory: %CD%
echo 📦 Checking if node_modules exists...

if not exist "node_modules" (
    echo ⚠️  node_modules not found
    echo 📦 Installing dependencies...
    npm install
    if errorlevel 1 (
        echo ❌ npm install failed
        pause
        exit /b 1
    )
) else (
    echo ✅ node_modules found
)

echo 🌐 Starting development server...
echo 🔗 Frontend will be available at: http://localhost:5173
echo 🔌 Backend should be running at: http://localhost:8000
echo 🛑 Press Ctrl+C to stop
echo ----------------------------------------

npm run dev

if errorlevel 1 (
    echo ❌ Failed to start frontend
    pause
    exit /b 1
)

pause