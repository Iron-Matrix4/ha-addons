ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM $BUILD_FROM

# Install spotifyd and dependencies from Alpine repos
RUN apk add --no-cache \
    alsa-lib \
    dbus \
    pulseaudio \
    pulseaudio-alsa \
    spotifyd

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
