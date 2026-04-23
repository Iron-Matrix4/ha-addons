#!/usr/bin/with-contenv bashio

VAULT_PATH=$(bashio::config 'vault_path')
RESOLUTION=$(bashio::config 'resolution')

bashio::log.info "Starting Obsidian addon..."
bashio::log.info "Vault path: $VAULT_PATH"
bashio::log.info "Resolution: $RESOLUTION"

mkdir -p "$VAULT_PATH"

WIDTH=$(echo "$RESOLUTION" | cut -d'x' -f1)
HEIGHT=$(echo "$RESOLUTION" | cut -d'x' -f2)

bashio::log.info "Starting Xvfb at ${WIDTH}x${HEIGHT}..."
Xvfb :99 -screen 0 "${WIDTH}x${HEIGHT}x24" -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 2

bashio::log.info "Starting Openbox..."
openbox &
sleep 1

# Verify the Obsidian binary exists
OBSIDIAN_BIN="/opt/obsidian-extracted/obsidian"
if [ ! -f "$OBSIDIAN_BIN" ]; then
    bashio::log.error "Obsidian binary not found at $OBSIDIAN_BIN"
    bashio::log.error "Contents of /opt/obsidian-extracted/:"
    ls /opt/obsidian-extracted/ 2>&1 | while read line; do bashio::log.error "$line"; done
    exit 1
fi

launch_obsidian() {
    bashio::log.info "Launching Obsidian..."
    "$OBSIDIAN_BIN" \
        --no-sandbox \
        --disable-gpu \
        --disable-software-rasterizer \
        --disable-dev-shm-usage \
        --disable-setuid-sandbox \
        "$VAULT_PATH" \
        > /var/log/obsidian.log 2>&1 &
    OBSIDIAN_PID=$!
    bashio::log.info "Obsidian PID: $OBSIDIAN_PID"
}

launch_obsidian
sleep 4

# Log first few lines of obsidian output to help debug crashes
bashio::log.info "Obsidian startup output:"
head -20 /var/log/obsidian.log 2>/dev/null | while read line; do bashio::log.info "$line"; done

bashio::log.info "Starting VNC server..."
x11vnc -display :99 -nopw -xkb -ncache 10 \
    -ncache_cr -quiet -forever &
sleep 1

bashio::log.info "Starting noVNC on port 8080..."
websockify --web /usr/share/novnc 8080 localhost:5900 &

bashio::log.info "Obsidian is ready — open the sidebar panel to use it."

# Keep alive — restart Obsidian by PID if it exits
while true; do
    sleep 10
    if ! kill -0 "$OBSIDIAN_PID" 2>/dev/null; then
        bashio::log.warning "Obsidian (PID $OBSIDIAN_PID) exited. Last log lines:"
        tail -10 /var/log/obsidian.log 2>/dev/null | while read line; do bashio::log.warning "$line"; done
        launch_obsidian
        sleep 4
    fi
done
