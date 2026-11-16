@echo off
REM One command start for Windows: double-click or run run.bat
cd /d "%~dp0"
if not exist venv python -m venv venv
call venv\Scripts\activate.bat
pip install -q -r backend\requirements.txt
cd backend
echo Open http://localhost:8000
uvicorn app.main:app --host 0.0.0.0 --port 8000
