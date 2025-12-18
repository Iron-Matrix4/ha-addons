# Jarvis AI Conversation Agent Integration

This custom integration enables the HTTP API connection for the [Jarvis AI Add-on](https://github.com/Iron-Matrix4/ha-addons).

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=jarvis_conversation)

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant.
2. Go to **Integrations** > Top right menu > **Custom repositories**.
3. Add `https://github.com/Iron-Matrix4/ha-addons` with category **Integration**.
4. Click **Install** on "Jarvis AI Conversation Agent".
5. Restart Home Assistant.

### Option 2: Manual

1. Copy the `custom_components/jarvis_conversation` folder to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. After restarting, click the button below or go to **Settings > Devices & Services > Add Integration**.

    [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=jarvis_conversation)

2. Search for **Jarvis AI**.
3. The configuration flow will start. If the Jarvis Add-on is installed, the URL should auto-fill to:
    `http://1066d494-jarvis-ai:10401`

4. Submit to finish setup.
