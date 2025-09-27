# Use a stable Python version (3.11) to avoid compilation errors
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    libffi-dev \
    libssl-dev \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel for prebuilt wheels
RUN pip install --upgrade pip wheel setuptools

# Copy requirements
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . /app

# Run the bot
CMD ["python3", "bot.py"]
