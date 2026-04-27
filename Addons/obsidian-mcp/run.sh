#!/usr/bin/with-contenv bashio

VAULT_PATH=$(bashio::config 'vault_path')

bashio::log.info "Starting Obsidian MCP Server..."
bashio::log.info "Vault: ${VAULT_PATH}"
bashio::log.info "Listening on :3005 (streamable HTTP)"

# supergateway wraps obsidian-mcp as HTTP/SSE
# Clients connect to http://192.168.4.10:3005/sse
while true; do
    supergateway \
        --port 3005 \
        --transportType http \
        --allowReinitialize \
        --stdio "obsidian-mcp ${VAULT_PATH}"
    bashio::log.warning "supergateway exited, restarting in 2s..."
    sleep 2
done
