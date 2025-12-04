#!/usr/bin/with-contenv bashio

# Export config options as environment variables
export GEMINI_API_KEY=$(bashio::config 'gemini_api_key')
export PICOVOICE_ACCESS_KEY=$(bashio::config 'picovoice_access_key')

# Persist machine-id to prevent Picovoice device limit exhaustion
if [ ! -f /data/machine-id ]; then
    bashio::log.info "Generating persistent machine-id..."
    if [ -f /etc/machine-id ]; then
        cp /etc/machine-id /data/machine-id
    else
        # Fallback if /etc/machine-id doesn't exist
        cat /proc/sys/kernel/random/uuid | tr -d '-' > /data/machine-id
    fi
else
    bashio::log.info "Restoring persistent machine-id..."
    cp /data/machine-id /etc/machine-id
fi

bashio::log.info "Starting Jarvis Assistant..."

# Run the python script
# Note: We will need to adapt Boot_Jarvis.py to run in this environment
python3 wyoming_jarvis.py
