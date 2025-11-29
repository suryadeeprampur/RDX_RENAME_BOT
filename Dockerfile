# Use slim base for smaller image
FROM python:3.11-slim-bullseye

# avoid buffering (helps with logs)
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# system packages needed to build wheels (installed + cleaned in one layer)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Upgrade pip/tools
RUN pip install --upgrade pip setuptools wheel

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create a non-root user and switch to it
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Expose port if your bot uses HTTP (remove if not)
# EXPOSE 8080

CMD ["python3", "bot.py"]
