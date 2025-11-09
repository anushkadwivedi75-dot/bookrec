#!/bin/bash

echo "========================================"
echo "Book Recommendation System"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Check and install dependencies
echo "Checking dependencies..."
if ! python3 -c "import pandas" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""

# Check for CSV files
if [ ! -f "Books.csv" ]; then
    echo "WARNING: Books.csv not found!"
fi

if [ ! -f "Ratings.csv" ]; then
    echo "WARNING: Ratings.csv not found!"
fi

echo ""

# Start application
echo "Starting application..."
echo ""
python3 app.py

