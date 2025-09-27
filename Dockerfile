# Use full Python image with all headers (avoids aiohttp build issues)
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    git \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all bot files
COPY . .

# Expose port if using Flask (default Flask port)
EXPOSE 5000

# Command to run your bot
CMD ["python3", "bot.py"]
