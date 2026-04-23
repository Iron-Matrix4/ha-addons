ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    openbox \
    wget \
    curl \
    ca-certificates \
    libglib2.0-0 \
    libgtk-3-0 \
    libnss3 \
    libxss1 \
    libxtst6 \
    libatspi2.0-0 \
    libdrm2 \
    libgbm1 \
    libxcb-dri3-0 \
    libxkbcommon0 \
    libasound2 \
    libcups2 \
    libpangocairo-1.0-0 \
    libfuse2 \
    procps \
    python3 \
    python3-websockify \
    novnc \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Download and extract Obsidian AppImage
ARG OBSIDIAN_VERSION=1.8.10
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        wget -q "https://github.com/obsidianmd/obsidian-releases/releases/download/v${OBSIDIAN_VERSION}/Obsidian-${OBSIDIAN_VERSION}.AppImage" \
            -O /opt/obsidian.AppImage; \
    elif [ "$ARCH" = "aarch64" ]; then \
        wget -q "https://github.com/obsidianmd/obsidian-releases/releases/download/v${OBSIDIAN_VERSION}/Obsidian-${OBSIDIAN_VERSION}-arm64.AppImage" \
            -O /opt/obsidian.AppImage; \
    fi && \
    chmod +x /opt/obsidian.AppImage && \
    cd /opt && ./obsidian.AppImage --appimage-extract && \
    mv squashfs-root obsidian-extracted && \
    rm obsidian.AppImage

# Set up nginx to serve noVNC and proxy websocket — all on port 8080
# nginx handles the HA ingress path prefix transparently
COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /root/.config/openbox
COPY openbox-rc.xml /root/.config/openbox/rc.xml

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 8080

CMD ["/run.sh"]
