#!/usr/bin/with-contenv bashio

VAULT_PATH=$(bashio::config 'vault_path')
RESOLUTION=$(bashio::config 'resolution')

bashio::log.info "Starting Obsidian addon..."
bashio::log.info "Vault path: $VAULT_PATH"
bashio::log.info "Resolution: $RESOLUTION"

# Create vault directory if it doesn't exist
mkdir -p "$VAULT_PATH"

# Parse resolution
WIDTH=$(echo "$RESOLUTION" | cut -d'x' -f1)
HEIGHT=$(echo "$RESOLUTION" | cut -d'x' -f2)

# Start virtual display
bashio::log.info "Starting Xvfb at ${WIDTH}x${HEIGHT}..."
Xvfb :99 -screen 0 "${WIDTH}x${HEIGHT}x24" -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 2

# Start window manager
bashio::log.info "Starting Openbox..."
openbox &
sleep 1

# Start Obsidian (extracted AppImage, no FUSE needed)
bashio::log.info "Launching Obsidian..."
/opt/obsidian-extracted/obsidian --no-sandbox --disable-gpu \
    --vault "$VAULT_PATH" \
    --disable-dev-shm-usage \
    2>/dev/null &
sleep 3

# Start VNC server
bashio::log.info "Starting VNC server..."
x11vnc -display :99 -nopw -listen localhost -xkb -ncache 10 \
    -ncache_cr -quiet -forever &
sleep 1

# Start noVNC websocket proxy on port 8080
bashio::log.info "Starting noVNC on port 8080..."
websockify --web /usr/share/novnc 8080 localhost:5900 &

bashio::log.info "Obsidian is ready — open the sidebar panel to use it."

# Keep container alive and restart Obsidian if it crashes
while true; do
    if ! pgrep -x obsidian > /dev/null; then
        bashio::log.warning "Obsidian exited, restarting..."
        /opt/obsidian-extracted/obsidian --no-sandbox --disable-gpu \
            --vault "$VAULT_PATH" \
            --disable-dev-shm-usage \
            2>/dev/null &
    fi
    sleep 10
done
