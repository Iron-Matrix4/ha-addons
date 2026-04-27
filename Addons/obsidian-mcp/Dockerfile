ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# supergateway: wraps stdio MCP server as HTTP/SSE server
# obsidian-mcp: reads/writes vault files directly
RUN npm install -g supergateway@3.4.3 obsidian-mcp@latest

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 3005

CMD ["/run.sh"]
