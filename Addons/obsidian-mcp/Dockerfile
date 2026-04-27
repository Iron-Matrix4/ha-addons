ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# mcp-obsidian: reads/writes vault files directly
# supergateway: wraps stdio MCP server as HTTP/SSE server
RUN npm install -g obsidian-mcp@latest supergateway@3.4.3

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 3005

CMD ["/run.sh"]
