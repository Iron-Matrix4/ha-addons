#!/usr/bin/with-contenv bashio
VERSION="1.1.2-optimized"

bashio::log.info "Starting Jarvis AI Add-on v$VERSION..."
bashio::log.info "Optimization Mode: Vertex System Instructions Enabled"

# Export configuration from HA add-on options
export GEMINI_API_KEY=$(bashio::config 'gemini_api_key')
export GEMINI_MODEL=$(bashio::config 'gemini_model')
export GCP_PROJECT_ID=$(bashio::config 'gcp_project_id')
export GOOGLE_SEARCH_API_KEY=$(bashio::config 'google_search_api_key')
export GOOGLE_SEARCH_ENGINE_ID=$(bashio::config 'google_search_engine_id')
export GOOGLE_MAPS_API_KEY=$(bashio::config 'google_maps_api_key')
export GOOGLE_CALENDAR_ID=$(bashio::config 'google_calendar_id')
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
export UNIFI_CONTROLLER_URL=$(bashio::config 'unifi_controller_url')
export UNIFI_CONTROLLER_API_TOKEN=$(bashio::config 'unifi_controller_api_token')
export UNIFI_CONTROLLER_USERNAME=$(bashio::config 'unifi_controller_username')
export UNIFI_CONTROLLER_PASSWORD=$(bashio::config 'unifi_controller_password')
export UNIFI_SITE_ID=$(bashio::config 'unifi_site_id')
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
    
    # DEBUG: List directories to debug mapping
    bashio::log.info "DEBUG: Listing /config:"
    ls -la /config || bashio::log.info "/config not accessible"
    bashio::log.info "DEBUG: Listing /share:"
    ls -la /share || bashio::log.info "/share not accessible"
    bashio::log.info "DEBUG: Listing /homeassistant:"
    ls -la /homeassistant || bashio::log.info "/homeassistant not accessible"

    # helper function to copy credentials
    function copy_creds() {
        if [ -f "$1" ]; then
            cp "$1" /data/gcp-credentials.json
            bashio::log.info "GCP credentials found at $1 and copied"
            return 0
        fi
        return 1
    }

    # Search for credentials in likely locations
    if copy_creds "/config/gcp-credentials.json"; then
        :
    elif copy_creds "/share/gcp-credentials.json"; then
        :
    elif copy_creds "/homeassistant/gcp-credentials.json"; then
        :
    elif copy_creds "/app/gcp-credentials.json"; then
        :
    else
        bashio::log.warning "GCP credentials file not found! Please upload gcp-credentials.json to /config, /share, or /homeassistant"
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
