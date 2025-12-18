# Home Assistant Add-ons Repository

[![Add Repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FIron-Matrix4%2Fha-addons)

A collection of custom add-ons for Home Assistant.

---

## Available Add-ons

### 🤖 [Jarvis AI](jarvis_ai/)

**J.A.R.V.I.S.** - Just A Rather Very Intelligent System

An intelligent voice-controlled conversation agent for Home Assistant, powered by Google Gemini. Features natural language control of your smart home, media systems, and information queries with the personality of Tony Stark's legendary AI assistant.

## 🧩 Component Installation (Optional)

To enable the HTTP API integration (which allows Jarvis to work without Wyoming or for advanced features), you need to install the custom component included in this repository.

1. **Copy the component**:
    Copy the `custom_components/jarvis_conversation` folder from this repository to your Home Assistant's `/config/custom_components/` directory.

    *If you are using SSH:*

    ```bash
    cp -r custom_components/jarvis_conversation /config/custom_components/
    ```

2. **Restart Home Assistant**:
    Restart Home Assistant to load the new component.

3. **Add Integration**:
    Go to **Settings > Devices & Services > Add Integration** and search for **"Jarvis AI Conversation Agent"**.
    The URL should auto-fill to `http://1066d494-jarvis-ai:10401`.

---

## 🔧 Advanced Configuration

**Features:**

- 🏠 Full smart home control (lights, climate, covers, locks)
- 🎵 Spotify integration via Spotcast
- 🎬 Media management (Radarr, Sonarr, Prowlarr, qBittorrent)
- 🌍 Web search and Google Maps travel time
- 📅 Google Calendar integration
- 🔒 UniFi Network queries
- 🧠 Persistent memory for preferences
- 🎭 Authentic J.A.R.V.I.S. personality

[📖 Full Documentation](jarvis_ai/README.md) | [🚀 Installation Guide](jarvis_ai/INSTALL.md)

---

### 🎵 [Spotify Player](spotify_player/)

A simple Spotify player add-on for Home Assistant.

---

## Installation

### One-Click Install (Recommended)

[![Add Repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FIron-Matrix4%2Fha-addons)

### Manual Install

1. Go to **Settings → Add-ons → Add-on Store**
2. Click the menu (⋮) → **Repositories**
3. Add: `https://github.com/Iron-Matrix4/ha-addons`
4. Click **Add** → **Close**
5. Refresh and find the add-ons in the store

---

## Support

For issues or feature requests, please [open an issue](https://github.com/Iron-Matrix4/ha-addons/issues).

---

## License

MIT License
