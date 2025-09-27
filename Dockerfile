# Use a stable Python version with prebuilt wheels
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for compiling Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    libffi-dev \
    libssl-dev \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . /app

# Expose port for Flask if needed
EXPOSE 5000

# Run the bot
CMD ["python3", "bot.py"]
