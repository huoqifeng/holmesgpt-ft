FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy training engine code
COPY training_engine/ ./training_engine/

# Set working directory to training_engine
WORKDIR /app/training_engine

# Expose port for Ray dashboard
EXPOSE 8265

# Default command
CMD ["python3", "convert.py"]