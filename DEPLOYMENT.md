# Deployment Guide for Book Recommendation System

This guide covers various deployment options for the Book Recommendation System.

## Prerequisites

- Python 3.8 or higher
- Required CSV files: `Books.csv`, `Ratings.csv`, `Users.csv` (optional)
- All dependencies from `requirements.txt`

## Option 1: Local Deployment (Simplest)

### Steps:

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Place CSV files in the project directory:**
   - `Books.csv`
   - `Ratings.csv`
   - `Users.csv` (optional)

3. **Run the application:**
```bash
python app.py
```

The GUI will launch automatically.

## Option 2: Standalone Executable (Windows/Mac/Linux)

Create a standalone executable that can run without Python installed.

### Using PyInstaller:

1. **Install PyInstaller:**
```bash
pip install pyinstaller
```

2. **Create executable:**
```bash
pyinstaller --name="BookRecommendationSystem" --windowed --onefile --add-data "Books.csv;." --add-data "Ratings.csv;." --add-data "Users.csv;." app.py
```

**For Linux/Mac, use colons instead of semicolons:**
```bash
pyinstaller --name="BookRecommendationSystem" --windowed --onefile --add-data "Books.csv:." --add-data "Ratings.csv:." --add-data "Users.csv:." app.py
```

3. **Find the executable:**
   - Windows: `dist/BookRecommendationSystem.exe`
   - Mac/Linux: `dist/BookRecommendationSystem`

### Create a spec file for better control:

Create `BookRecommendationSystem.spec`:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Books.csv', '.'),
        ('Ratings.csv', '.'),
        ('Users.csv', '.'),
    ],
    hiddenimports=[
        'pandas',
        'numpy',
        'sklearn',
        'PIL',
        'requests',
        'tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BookRecommendationSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one
)
```

Then build:
```bash
pyinstaller BookRecommendationSystem.spec
```

## Option 3: Web Deployment with Flask

Convert the Tkinter GUI to a web application.

### Create `app_web.py`:

```python
"""
Web version of Book Recommendation System using Flask
"""

from flask import Flask, render_template, request, jsonify
from recommendation_engine import RecommendationEngine
import os

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Initialize engine (load once at startup)
engine = None

@app.before_first_request
def initialize_engine():
    global engine
    try:
        engine = RecommendationEngine("Books.csv", "Ratings.csv")
        print("Engine initialized successfully!")
    except Exception as e:
        print(f"Error initializing engine: {e}")
        engine = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/popular', methods=['GET'])
def get_popular_books():
    try:
        n = request.args.get('n', 50, type=int)
        books = engine.get_popular_books(n)
        return jsonify(books.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        book_title = data.get('book_title')
        n = data.get('n', 10)
        
        recommendations = engine.get_recommendations(book_title, n)
        book_info = engine.get_book_info(book_title)
        
        return jsonify({
            'book_info': book_info,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_books():
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 20, type=int)
        books = engine.search_books(query, limit)
        return jsonify(books)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Create `templates/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Recommendation System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #4a90e2;
            text-align: center;
        }
        .search-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: 70%;
            padding: 10px;
            font-size: 16px;
        }
        button {
            padding: 10px 20px;
            background: #4a90e2;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
        .books-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
        }
        .book-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .loading {
            text-align: center;
            padding: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Book Recommendation System</h1>
        
        <div class="search-section">
            <input type="text" id="searchInput" placeholder="Search for a book...">
            <button onclick="searchBook()">Search</button>
        </div>
        
        <div id="results"></div>
    </div>

    <script>
        async function searchBook() {
            const query = document.getElementById('searchInput').value;
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">Loading...</div>';
            
            try {
                const response = await fetch('/api/recommend', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({book_title: query, n: 10})
                });
                const data = await response.json();
                
                if (data.error) {
                    resultsDiv.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }
                
                let html = `<h2>Searched: ${data.book_info?.Book-Title || query}</h2>`;
                html += '<div class="books-grid">';
                data.recommendations.forEach(rec => {
                    html += `
                        <div class="book-card">
                            <h3>${rec.book}</h3>
                            <p>Similarity: ${(rec.similarity * 100).toFixed(2)}%</p>
                        </div>
                    `;
                });
                html += '</div>';
                resultsDiv.innerHTML = html;
            } catch (error) {
                resultsDiv.innerHTML = `<p>Error: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```

### Run Flask app:

```bash
pip install flask
python app_web.py
```

Visit `http://localhost:5000` in your browser.

## Option 4: Docker Deployment

### Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port (if using web version)
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
```

### Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  book-recommendation:
    build: .
    container_name: book-recommendation-app
    volumes:
      - ./Books.csv:/app/Books.csv
      - ./Ratings.csv:/app/Ratings.csv
      - ./Users.csv:/app/Users.csv
    ports:
      - "5000:5000"  # If using web version
    environment:
      - PYTHONUNBUFFERED=1
```

### Build and run:

```bash
docker-compose up --build
```

## Option 5: Cloud Deployment

### Heroku:

1. **Create `Procfile`:**
```
web: python app_web.py
```

2. **Create `runtime.txt`:**
```
python-3.9.0
```

3. **Deploy:**
```bash
heroku create book-recommendation-app
git push heroku main
```

### AWS EC2:

1. **Launch EC2 instance**
2. **SSH into instance:**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. **Install dependencies:**
```bash
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt
```

4. **Upload files:**
```bash
scp -i your-key.pem -r . ubuntu@your-ec2-ip:/home/ubuntu/bookrec
```

5. **Run with screen or systemd:**
```bash
screen -S bookrec
python3 app.py
```

### Google Cloud Platform:

1. **Create App Engine app:**
```bash
gcloud app create
```

2. **Create `app.yaml`:**
```yaml
runtime: python39

handlers:
- url: /.*
  script: auto
```

3. **Deploy:**
```bash
gcloud app deploy
```

## Option 6: Create a Startup Script

### Windows (`start.bat`):

```batch
@echo off
echo Starting Book Recommendation System...
python app.py
pause
```

### Linux/Mac (`start.sh`):

```bash
#!/bin/bash
echo "Starting Book Recommendation System..."
python3 app.py
```

Make it executable:
```bash
chmod +x start.sh
```

## Performance Considerations

1. **Data Loading:**
   - Initial load takes 30-60 seconds
   - Consider pre-loading data in production
   - Use caching for frequently accessed data

2. **Memory:**
   - Requires ~2-4GB RAM for full dataset
   - Consider using smaller datasets for testing

3. **Image Loading:**
   - Images load asynchronously
   - Consider CDN for production
   - Implement image compression

## Security Considerations

1. **Input Validation:**
   - Validate all user inputs
   - Sanitize search queries
   - Handle SQL injection (if using database)

2. **File Access:**
   - Restrict file system access
   - Validate file paths
   - Use environment variables for sensitive data

3. **Rate Limiting:**
   - Implement rate limiting for API endpoints
   - Prevent abuse of recommendation system

## Troubleshooting

### Common Issues:

1. **"Module not found" errors:**
   - Run `pip install -r requirements.txt`
   - Check Python version (3.8+)

2. **CSV files not found:**
   - Ensure CSV files are in the same directory as `app.py`
   - Check file permissions

3. **Memory errors:**
   - Reduce dataset size
   - Increase system RAM
   - Use data streaming for large files

4. **Image loading failures:**
   - Check internet connection
   - Some URLs may be broken (expected)
   - Images load asynchronously (may take time)

## Next Steps

1. Choose deployment method based on your needs
2. Test thoroughly before production deployment
3. Monitor performance and memory usage
4. Consider adding logging and error tracking
5. Implement user authentication if needed
6. Add database support for scalability

## Support

For issues or questions, refer to the README.md or open an issue on the repository.

