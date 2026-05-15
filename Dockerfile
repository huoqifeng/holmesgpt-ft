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

# Install TensorBoard for monitoring
RUN pip install tensorboard

# Copy training engine code
COPY training_engine/ ./training_engine/

# Set working directory to training_engine
WORKDIR /app/training_engine

# Expose ports for Ray dashboard and TensorBoard
EXPOSE 8265
EXPOSE 6006

# Default command
CMD ["python3", "convert.py"]