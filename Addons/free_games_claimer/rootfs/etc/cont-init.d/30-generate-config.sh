#!/usr/bin/env bashio
# shellcheck shell=bash
# Generate config.env from addon configuration

set -e

CONFIG_HOME="$(bashio::config "CONFIG_LOCATION")"
CONFIG_HOME="$(dirname "$CONFIG_HOME")"

# Get credentials from addon config
EPIC_EMAIL="$(bashio::config "EPIC_EMAIL" || echo "")"
EPIC_PASSWORD="$(bashio::config "EPIC_PASSWORD" || echo "")"
GOG_EMAIL="$(bashio::config "GOG_EMAIL" || echo "")"
GOG_PASSWORD="$(bashio::config "GOG_PASSWORD" || echo "")"
PRIME_EMAIL="$(bashio::config "PRIME_EMAIL" || echo "")"
PRIME_PASSWORD="$(bashio::config "PRIME_PASSWORD" || echo "")"

bashio::log.info "Generating config.env from addon settings..."

# Create config.env with credentials from addon config
cat > "$CONFIG_HOME/config.env" <<EOF
# Browser settings
HEIGHT=1280
LOGIN_TIMEOUT=180
NOTIFY_TITLE='Free Games Claimer'
SHOW=0
TIMEOUT=60
WIDTH=1280

# Epic Games credentials (from addon config)
$([ -n "$EPIC_EMAIL" ] && [ "$EPIC_EMAIL" != '""' ] && echo "EMAIL=$EPIC_EMAIL" || echo "# EMAIL=")
$([ -n "$EPIC_PASSWORD" ] && [ "$EPIC_PASSWORD" != '""' ] && echo "PASSWORD=$EPIC_PASSWORD" || echo "# PASSWORD=")

# GOG credentials (from addon config)
$([ -n "$GOG_EMAIL" ] && [ "$GOG_EMAIL" != '""' ] && echo "GOG_EMAIL=$GOG_EMAIL" || echo "# GOG_EMAIL=")
$([ -n "$GOG_PASSWORD" ] && [ "$GOG_PASSWORD" != '""' ] && echo "GOG_PASSWORD=$GOG_PASSWORD" || echo "# GOG_PASSWORD=")

# Prime Gaming credentials (from addon config)  
$([ -n "$PRIME_EMAIL" ] && [ "$PRIME_EMAIL" != '""' ] && echo "AMAZON_EMAIL=$PRIME_EMAIL" || echo "# AMAZON_EMAIL=")
$([ -n "$PRIME_PASSWORD" ] && [ "$PRIME_PASSWORD" != '""' ] && echo "AMAZON_PASSWORD=$PRIME_PASSWORD" || echo "# AMAZON_PASSWORD=")

# Notification settings
# Uncomment and configure for Home Assistant notifications:
# APPRISE_URL=homeassistant://192.168.4.10:8123/YOUR_LONG_LIVED_TOKEN

# Other notification examples:
# APPRISE_URL=discord://webhook_id/webhook_token
# APPRISE_URL=tgram://bot_token/chat_id
EOF

chmod 644 "$CONFIG_HOME/config.env"
bashio::log.info "config.env generated successfully from addon configuration"

# Show which platforms have credentials configured (properly check for non-empty)
if [ -n "$EPIC_EMAIL" ] && [ "$EPIC_EMAIL" != '""' ]; then
    bashio::log.info "✓ Epic Games credentials configured"
else
    bashio::log.warning "✗ Epic Games credentials not set - configure EPIC_EMAIL and EPIC_PASSWORD in addon settings"
fi

if [ -n "$GOG_EMAIL" ] && [ "$GOG_EMAIL" != '""' ]; then
    bashio::log.info "✓ GOG credentials configured"
else
    bashio::log.warning "✗ GOG credentials not set - configure GOG_EMAIL and GOG_PASSWORD in addon settings"
fi

if [ -n "$PRIME_EMAIL" ] && [ "$PRIME_EMAIL" != '""' ]; then
    bashio::log.info "✓ Prime Gaming credentials configured"
else
    bashio::log.warning "✗ Prime Gaming credentials not set - configure PRIME_EMAIL and PRIME_PASSWORD in addon settings"
fi
