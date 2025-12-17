# Use Debian-based Python image
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11
FROM ${BUILD_FROM}

# Install system dependencies using apt-get (Debian)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    python3-pip \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application files
COPY . /app/

# Copy run script
COPY run.sh /

# Make run script executable
RUN chmod +x /run.sh

# Create data directory for persistent storage
RUN mkdir -p /data

# Note: GCP credentials for Vertex AI mode should be provided via Home Assistant options/secrets
# Users can mount credentials file or provide service account JSON in addon configuration

# Expose Wyoming protocol port and HTTP API port
EXPOSE 10400 10401

# Run via the startup script (which sets environment variables)
CMD ["/run.sh"]
