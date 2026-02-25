@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Production Server...
python wsgi.py
pause
