#!/usr/bin/with-contenv bashio

VAULT_PATH=$(bashio::config 'vault_path')
RESOLUTION=$(bashio::config 'resolution')

bashio::log.info "Starting Obsidian addon..."
mkdir -p "$VAULT_PATH"

WIDTH=$(echo "$RESOLUTION" | cut -d'x' -f1)
HEIGHT=$(echo "$RESOLUTION" | cut -d'x' -f2)

# Start virtual framebuffer
bashio::log.info "Starting Xvfb ${WIDTH}x${HEIGHT}..."
Xvfb :99 -screen 0 "${WIDTH}x${HEIGHT}x24" -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 2

# Start window manager
openbox &
sleep 1

OBSIDIAN_BIN="/opt/obsidian-extracted/obsidian"

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

bashio::log.info "Obsidian startup output:"
head -10 /var/log/obsidian.log 2>/dev/null | while read line; do bashio::log.info "$line"; done

# x11vnc: export the X display as a raw VNC server on localhost:5900
bashio::log.info "Starting x11vnc..."
x11vnc -display :99 -nopw -forever -shared -rfbport 5900 -quiet &
sleep 1

# websockify: wrap VNC port 5900 as a WebSocket on port 5901
# nginx then proxies /websockify → 5901
bashio::log.info "Starting websockify on 5901..."
websockify 5901 localhost:5900 &
sleep 1

# nginx: serves noVNC files + proxies /websockify → websockify
bashio::log.info "Starting nginx on port 8080..."
nginx

bashio::log.info "Obsidian is ready — open the sidebar panel to use it."

while true; do
    sleep 10
    if ! kill -0 "$OBSIDIAN_PID" 2>/dev/null; then
        bashio::log.warning "Obsidian exited, restarting..."
        tail -5 /var/log/obsidian.log 2>/dev/null | while read line; do bashio::log.warning "$line"; done
        launch_obsidian
        sleep 4
    fi
done
