#!/usr/bin/env bashio
# shellcheck shell=bash
set -e

# Define ASF version and paths
ASF_VERSION="6.0.2.2" # Pinning a stable version to avoid immediate update loops, or use "latest"
ASF_DIR="/data/asf"
CONFIG_DIR="/config/asf"

# Ensure directories exist
mkdir -p "$ASF_DIR"
mkdir -p "$CONFIG_DIR/config"
mkdir -p "$CONFIG_DIR/plugins"

# Download and install ASF if not present or empty
if [ ! -f "$ASF_DIR/ArchiSteamFarm.dll" ]; then
    bashio::log.info "Installing ArchiSteamFarm (ASF)..."
    
    # Download latest release (or pinned)
    # Using generic linux-x64.zip
    curl -L -o /tmp/ASF.zip "https://github.com/JustArchiNET/ArchiSteamFarm/releases/latest/download/ASF-linux-x64.zip"
    
    unzip -o /tmp/ASF.zip -d "$ASF_DIR"
    rm /tmp/ASF.zip
    
    chmod +x "$ASF_DIR/ArchiSteamFarm.dll"
    bashio::log.info "ASF installed."
fi

# Download FreePackages plugin
if [ ! -f "$ASF_DIR/plugins/FreePackages.dll" ]; then
    bashio::log.info "Installing FreePackages plugin..."
    curl -L -o /tmp/FreePackages.zip "https://github.com/Citrinate/FreePackages/releases/latest/download/FreePackages.zip"
    unzip -o /tmp/FreePackages.zip -d "$ASF_DIR/plugins"
    rm /tmp/FreePackages.zip
    bashio::log.info "FreePackages plugin installed."
fi

# Symlink config directory if needed (ASF expects config in its own dir usually, or we pass --path)
# But standard ASF looks in ./config relative to executable.
# We'll rely on command line args in run.sh or symlink.
# Let's symlink /config/asf/config to /data/asf/config for persistence
rm -rf "$ASF_DIR/config"
ln -s "$CONFIG_DIR/config" "$ASF_DIR/config"

bashio::log.info "ASF setup complete."
