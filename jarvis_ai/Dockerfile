ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies for Audio and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy all application files
COPY . /app

# Copy run script and make executable
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
