@echo off
echo ========================================
echo Book Recommendation System
echo ========================================
echo.
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo.
echo Checking dependencies...
pip show pandas >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Checking for CSV files...
if not exist "Books.csv" (
    echo WARNING: Books.csv not found!
)
if not exist "Ratings.csv" (
    echo WARNING: Ratings.csv not found!
)

echo.
echo Starting application...
echo.
python app.py

pause

