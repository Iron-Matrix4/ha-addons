ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive

# Install display stack + dependencies for Obsidian AppImage
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    openbox \
    novnc \
    websockify \
    wget \
    curl \
    ca-certificates \
    libglib2.0-0 \
    libgtk-3-0 \
    libnotify4 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    libatspi2.0-0 \
    libdrm2 \
    libgbm1 \
    libxcb-dri3-0 \
    libxkbcommon0 \
    fuse \
    libfuse2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Download latest Obsidian AppImage
ARG OBSIDIAN_VERSION=1.8.10
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        wget -q "https://github.com/obsidianmd/obsidian-releases/releases/download/v${OBSIDIAN_VERSION}/Obsidian-${OBSIDIAN_VERSION}.AppImage" \
            -O /opt/obsidian.AppImage; \
    elif [ "$ARCH" = "aarch64" ]; then \
        wget -q "https://github.com/obsidianmd/obsidian-releases/releases/download/v${OBSIDIAN_VERSION}/Obsidian-${OBSIDIAN_VERSION}-arm64.AppImage" \
            -O /opt/obsidian.AppImage; \
    fi && \
    chmod +x /opt/obsidian.AppImage

# Extract AppImage so FUSE isn't needed at runtime (works in Docker without privileged)
RUN cd /opt && \
    ./obsidian.AppImage --appimage-extract && \
    mv squashfs-root obsidian-extracted && \
    rm obsidian.AppImage

# noVNC is at /usr/share/novnc — create a simple index redirect
RUN ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Openbox minimal config (no decorations, black bg)
RUN mkdir -p /root/.config/openbox
COPY openbox-rc.xml /root/.config/openbox/rc.xml

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 8080

CMD ["/run.sh"]
