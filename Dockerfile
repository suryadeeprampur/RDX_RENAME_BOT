# Use a slim Python image for faster builds
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    git \
    ffmpeg \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements.txt
COPY requirements.txt /app/

# Install Python dependencies
# Ensure compatible versions: python-telegram-bot==13.15 needs cachetools==4.2.2
RUN pip install -r requirements.txt

# Copy all bot code
COPY . /app

# Start the bot
CMD ["python3", "bot.py"]
