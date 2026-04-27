#!/usr/bin/with-contenv bashio

VAULT_PATH=$(bashio::config 'vault_path')

bashio::log.info "Starting Obsidian MCP Server..."
bashio::log.info "Vault: ${VAULT_PATH}"
bashio::log.info "Listening on :3005 (SSE)"

# Restart supergateway fresh on every disconnect so new clients always get a clean process
while true; do
    supergateway \
        --port 3005 \
        --outputTransport sse \
        --cors \
        --healthEndpoint /health \
        --stdio "obsidian-mcp ${VAULT_PATH}" 2>&1 | \
    while IFS= read -r line; do
        echo "$line"
        if echo "$line" | grep -q "SSE connection closed"; then
            bashio::log.warning "Client disconnected — restarting supergateway for clean state"
            pkill -f "supergateway" 2>/dev/null
        fi
    done
    sleep 1
done
