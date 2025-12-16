#!/usr/bin/with-contenv bashio

echo "Starting Jarvis AI Add-on..."

# Export configuration from HA add-on options
export GEMINI_API_KEY=$(bashio::config 'gemini_api_key')
export GEMINI_MODEL=$(bashio::config 'gemini_model')
export GCP_PROJECT_ID=$(bashio::config 'gcp_project_id')
export GOOGLE_SEARCH_API_KEY=$(bashio::config 'google_search_api_key')
export GOOGLE_SEARCH_ENGINE_ID=$(bashio::config 'google_search_engine_id')
export GOOGLE_MAPS_API_KEY=$(bashio::config 'google_maps_api_key')
export SPOTIPY_CLIENT_ID=$(bashio::config 'spotify_client_id')
export SPOTIPY_CLIENT_SECRET=$(bashio::config 'spotify_client_secret')
export RADARR_URL=$(bashio::config 'radarr_url')
export RADARR_API_KEY=$(bashio::config 'radarr_api_key')
export SONARR_URL=$(bashio::config 'sonarr_url')
export SONARR_API_KEY=$(bashio::config 'sonarr_api_key')
export QBITTORRENT_URL=$(bashio::config 'qbittorrent_url')
export QBITTORRENT_USERNAME=$(bashio::config 'qbittorrent_username')
export QBITTORRENT_PASSWORD=$(bashio::config 'qbittorrent_password')
export PROWLARR_URL=$(bashio::config 'prowlarr_url')
export PROWLARR_API_KEY=$(bashio::config 'prowlarr_api_key')
export UNIFI_WAN_SENSOR=$(bashio::config 'unifi_wan_sensor')

# Home Assistant connection (auto-provided by add-on framework)
export HA_URL="http://supervisor/core"

# Validate configuration - support both AI Studio and Vertex AI
if [ -z "$GCP_PROJECT_ID" ]; then
    # AI Studio mode - require API key
    if [ -z "$GEMINI_API_KEY" ]; then
        bashio::log.error "Either Gemini API Key (AI Studio) or GCP Project ID (Vertex AI) is required!"
        bashio::log.error "DEBUG: GEMINI_API_KEY value: '$GEMINI_API_KEY'"
        bashio::log.error "DEBUG: GCP_PROJECT_ID value: '$GCP_PROJECT_ID'"
        exit 1
    fi
    bashio::log.info "Using AI Studio mode with API Key"
    bashio::log.info "DEBUG: First 10 chars: ${GEMINI_API_KEY:0:10}..."
else
    # Vertex AI mode - use project ID and credentials
    bashio::log.info "Using Vertex AI mode"
    bashio::log.info "GCP Project ID: $GCP_PROJECT_ID"
    
    # Copy credentials to data directory if it exists
    if [ -f "/app/gcp-credentials.json" ]; then
        cp /app/gcp-credentials.json /data/gcp-credentials.json
        bashio::log.info "GCP credentials file found and copied"
    else
        bashio::log.warning "GCP credentials file not found at /app/gcp-credentials.json"
    fi
fi

bashio::log.info "Home Assistant URL: $HA_URL"

# Optional services
if [ -n "$GOOGLE_SEARCH_API_KEY" ]; then
    bashio::log.info "Google Custom Search: Configured ✓"
else
    bashio::log.warning "Google Custom Search: Not configured (web search disabled)"
fi

if [ -n "$GOOGLE_MAPS_API_KEY" ]; then
    bashio::log.info "Google Maps: Configured ✓"
else
    bashio::log.warning "Google Maps: Not configured (travel time disabled)"
fi

if [ -n "$SPOTIPY_CLIENT_ID" ]; then
    bashio::log.info "Spotify: Configured ✓"
else
    bashio::log.warning "Spotify: Not configured (optional)"
fi

if [ -n "$RADARR_URL" ]; then
    bashio::log.info "Radarr: Configured ✓"
else
    bashio::log.warning "Radarr: Not configured (optional)"
fi

if [ -n "$SONARR_URL" ]; then
    bashio::log.info "Sonarr: Configured ✓"
else
    bashio::log.warning "Sonarr: Not configured (optional)"
fi

if [ -n "$QBITTORRENT_URL" ]; then
    bashio::log.info "qBittorrent: Configured ✓"
else
    bashio::log.warning "qBittorrent: Not configured (optional)"
fi

if [ -n "$PROWLARR_URL" ]; then
    bashio::log.info "Prowlarr: Configured ✓"
else
    bashio::log.warning "Prowlarr: Not configured (optional)"
fi

bashio::log.info "All configuration loaded successfully"
bashio::log.info "Starting Jarvis conversation server..."

# Run the Python application
exec python3 /app/main.py
