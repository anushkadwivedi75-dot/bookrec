FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create templates directory
RUN mkdir -p templates

# Expose port
EXPOSE 5000

# Run application (web version)
# For GUI version, use: CMD ["python", "app.py"]
CMD ["python", "app_web.py"]

