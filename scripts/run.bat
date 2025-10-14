@echo off
REM Foolproof startup script for fba-bench

echo Starting FBA Bench (Simple)...
REM Use the simple docker-compose file
docker-compose -f docker-compose-simple.yml up --build -d

echo.
echo ✅ FBA Bench is starting up!
echo ---------------------------------
echo 🌐 Frontend will be available at: http://localhost:5173
echo ⚙️ API docs will be available at: http://localhost:8000/docs
echo ---------------------------------