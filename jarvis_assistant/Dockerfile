ARG BUILD_FROM
FROM $BUILD_FROM
# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    espeak-ng \
    build-essential \
    python3-dev \
    portaudio19-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy data for add-on
COPY . /app
WORKDIR /app

# Install Python requirements
# Break system packages to allow pip install
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

# Reassemble split model parts
RUN cat /app/piper_models/jarvis-high.onnx.part* > /app/piper_models/jarvis-high.onnx \
    && rm /app/piper_models/jarvis-high.onnx.part*

# Make run script executable
RUN chmod a+x run.sh

CMD [ "/app/run.sh" ]
