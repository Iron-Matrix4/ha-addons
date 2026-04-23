#!/usr/bin/with-contenv bashio

VAULT_PATH=$(bashio::config 'vault_path')
RESOLUTION=$(bashio::config 'resolution')

bashio::log.info "Starting Obsidian addon..."
bashio::log.info "Vault path: $VAULT_PATH"
bashio::log.info "Resolution: $RESOLUTION"

mkdir -p "$VAULT_PATH"

WIDTH=$(echo "$RESOLUTION" | cut -d'x' -f1)
HEIGHT=$(echo "$RESOLUTION" | cut -d'x' -f2)

# Update KasmVNC resolution config
sed -i "s/width: 1280/width: $WIDTH/" /root/.vnc/kasmvnc.yaml
sed -i "s/height: 800/height: $HEIGHT/" /root/.vnc/kasmvnc.yaml

# KasmVNC needs a password file even with auth disabled
mkdir -p /root/.vnc
echo "" | vncpasswd -f > /root/.vnc/passwd 2>/dev/null || true
chmod 600 /root/.vnc/passwd 2>/dev/null || true

# Start KasmVNC (serves its own web UI on port 8080)
bashio::log.info "Starting KasmVNC on port 8080..."
vncserver :1 \
    -geometry "${WIDTH}x${HEIGHT}" \
    -depth 24 \
    -websocketPort 8080 \
    -httpd /usr/share/kasmvnc/www \
    -noxstartup \
    -nopw \
    -SecurityTypes None \
    2>&1 | while read line; do bashio::log.info "$line"; done &
export DISPLAY=:1
sleep 3

# Start window manager
bashio::log.info "Starting Openbox..."
DISPLAY=:1 openbox &
sleep 1

OBSIDIAN_BIN="/opt/obsidian-extracted/obsidian"

launch_obsidian() {
    bashio::log.info "Launching Obsidian..."
    DISPLAY=:1 "$OBSIDIAN_BIN" \
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
