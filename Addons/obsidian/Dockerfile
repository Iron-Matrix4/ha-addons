ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive

# Install KasmVNC dependencies and Obsidian deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
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
    python3-pip \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install KasmVNC
ARG KASMVNC_VERSION=1.3.3
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        wget -q "https://github.com/kasmtech/KasmVNC/releases/download/v${KASMVNC_VERSION}/kasmvncserver_bookworm_${KASMVNC_VERSION}_amd64.deb" -O /tmp/kasmvnc.deb; \
    elif [ "$ARCH" = "aarch64" ]; then \
        wget -q "https://github.com/kasmtech/KasmVNC/releases/download/v${KASMVNC_VERSION}/kasmvncserver_bookworm_${KASMVNC_VERSION}_arm64.deb" -O /tmp/kasmvnc.deb; \
    fi && \
    apt-get update && \
    apt-get install -y --no-install-recommends /tmp/kasmvnc.deb && \
    rm /tmp/kasmvnc.deb && \
    rm -rf /var/lib/apt/lists/*

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

# KasmVNC config directory
RUN mkdir -p /root/.vnc

COPY kasmvnc.yaml /root/.vnc/kasmvnc.yaml
COPY openbox-rc.xml /root/.config/openbox/rc.xml

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 8080

CMD ["/run.sh"]
