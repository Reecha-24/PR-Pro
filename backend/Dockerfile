# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory in container
WORKDIR /app

# Install system dependencies (if needed for build, e.g., gcc, libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Expose port 8000 for FastAPI main server
EXPOSE 8000

# Default command runs the FastAPI backend server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
