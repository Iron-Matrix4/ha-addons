#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Spotify Player (spotifyd)..."

# Get configuration
SPOTIFY_USERNAME=$(bashio::config 'spotify_username')
SPOTIFY_PASSWORD=$(bashio::config 'spotify_password')
DEVICE_NAME=$(bashio::config 'device_name')
BITRATE=$(bashio::config 'bitrate')

# Validate required configuration
if [ -z "$SPOTIFY_USERNAME" ] || [ -z "$SPOTIFY_PASSWORD" ]; then
    bashio::log.error "Spotify username and password are required!"
    bashio::log.error "Please configure them in the add-on configuration."
    exit 1
fi

bashio::log.info "Device name: $DEVICE_NAME"
bashio::log.info "Bitrate: $BITRATE kbps"
bashio::log.info "Attempting authentication as: $SPOTIFY_USERNAME"

# Create spotifyd config file
CONFIG_FILE="/tmp/spotifyd.conf"

cat > "$CONFIG_FILE" << EOF
[global]
username = "$SPOTIFY_USERNAME"
password = "$SPOTIFY_PASSWORD"
backend = "pulseaudio"
device_name = "$DEVICE_NAME"
bitrate = $BITRATE
cache_path = "/data/cache"
volume_normalisation = true
normalisation_pregain = -10
device_type = "speaker"
use_mpris = false
EOF

bashio::log.info "Configuration file created"

# Start PulseAudio (we need audio subsystem even if no physical output)
bashio::log.info "Starting PulseAudio..."
pulseaudio --start --exit-idle-time=-1 --log-target=syslog 2>&1

# Start spotifyd with verbose logging
bashio::log.info "Starting spotifyd..."
bashio::log.info "Connecting to Spotify servers..."
bashio::log.info "Watch for 'Authenticated' message below:"

# Run spotifyd with config and verbose output
exec spotifyd --no-daemon --config-path "$CONFIG_FILE" --verbose
