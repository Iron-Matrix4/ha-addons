# Jarvis AI - Home Assistant Conversation Agent

<img src="icon.png" alt="Jarvis Logo" width="128">

**J.A.R.V.I.S.** - Just A Rather Very Intelligent System

An intelligent voice-controlled conversation agent for Home Assistant, powered by Google Gemini. Jarvis provides natural language control of your smart home, media systems, and information queries with the personality of Tony Stark's legendary AI assistant.

[![Add Repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FIron-Matrix4%2Fha-addons)

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Integrations](#integrations)
- [Example Commands](#example-commands)
- [Voice Pipeline Setup](#voice-pipeline-setup)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Privacy & Data](#privacy--data)

---

## Features

### 🏠 Smart Home Control

| Feature | Description |
|---------|-------------|
| **Full Entity Control** | Turn on/off lights, switches, fans, covers, locks, and more |
| **Climate Management** | Set temperatures, change HVAC modes, turn up/down thermostats |
| **Brightness & Colors** | Dim lights, change colors by name or RGB values |
| **Cover Control** | Open/close blinds, garage doors, and covers |
| **Smart Follow-ups** | "Turn it off" remembers what "it" refers to |
| **Entity Search** | Find entities by partial name when you don't know the exact ID |
| **Appliance Status** | Get smart status with time remaining (e.g., washing machine) |
| **Person Location** | Track where people are (home, away, at specific zones) |

### 🎵 Media & Entertainment

| Feature | Description |
|---------|-------------|
| **Spotify** | Play songs, artists, albums, or playlists via Spotcast |
| **Radarr** | Add movies, check library stats, view recent downloads |
| **Sonarr** | Add TV series, check missing episodes, view download history |
| **Prowlarr** | Check indexer status and stats |
| **qBittorrent** | Monitor download speeds, active torrents, completed downloads |

### 🌐 Information & Knowledge

| Feature | Description |
|---------|-------------|
| **Web Search** | Answer general knowledge questions via Google Custom Search |
| **Weather** | Current conditions and rain forecasts with umbrella recommendations |
| **Travel Time** | Real-time traffic estimates between locations via Google Maps |
| **Contextual Answers** | Combine HA sensor data with web knowledge (e.g., "Is my fish tank too hot?") |
| **Camera Analysis** | Analyze camera snapshots using Gemini Vision |

### 📅 Productivity

| Feature | Description |
|---------|-------------|
| **Google Calendar** | Add events and list upcoming schedule |
| **Location Reminders** | "Remind me when I get home" |
| **Timers** | Set countdown timers |
| **Current Time** | Get current date/time |

### 🔒 Network & Security

| Feature | Description |
|---------|-------------|
| **UniFi Network** | WAN IP, connected devices, uptime, bandwidth via HA sensors |
| **UniFi Controller** | Advanced: DHCP leases, next available IP, firewall rules, port forwards |
| **VPN Status** | Check if your download VM's VPN is connected |

### 🧠 Memory & Personality

| Feature | Description |
|---------|-------------|
| **Persistent Memory** | Remembers your preferences across restarts |
| **Preference Storage** | Save and recall any information ("Remember my partner's name is Alex") |
| **J.A.R.V.I.S. Personality** | Witty, helpful, slightly sarcastic - just like Tony Stark's AI |

---

## Quick Start

### Option 1: One-Click Install (Recommended)

[![Add Repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FIron-Matrix4%2Fha-addons)

1. Click the button above to add the repository
2. Go to **Settings → Add-ons → Add-on Store**
3. Find "Jarvis AI" → **Install**
4. Configure your Gemini API key and **Start**

### Option 2: Manual Install

1. **Add repository manually**:
   - Settings → Add-ons → Add-on Store → ⋮ → Repositories
   - Add: `https://github.com/Iron-Matrix4/ha-addons`

2. **Install the add-on**:
   - Reload, find "Jarvis AI" → Install

3. **Configure API Key**:
   - Go to Configuration tab
   - Enter your Gemini API Key
   - Save and Start

4. **Create Voice Assistant**:
   - Settings → Voice assistants → Add Assistant
   - Set Conversation agent to "Jarvis AI"

See [INSTALL.md](INSTALL.md) for detailed step-by-step instructions.

---

## Configuration

### AI Provider (Choose One)

#### Option A: Google AI Studio (Recommended for Personal Use)

| Setting | Description | How to Get |
|---------|-------------|------------|
| `gemini_api_key` | Your Gemini API key | [AI Studio](https://aistudio.google.com/apikey) - Free tier available |

#### Option B: Google Vertex AI (Enterprise/Advanced)

| Setting | Description |
|---------|-------------|
| `gcp_project_id` | Your Google Cloud Project ID |

> **Note**: Vertex AI requires a GCP service account credentials file. Place `gcp-credentials.json` in the add-on's data directory (`/data/gcp-credentials.json`).

### Model Selection

| Model | Speed | Intelligence | Cost | Best For |
|-------|-------|--------------|------|----------|
| `gemini-2.5-flash-lite` | ⚡⚡⚡ | ⭐⭐ | 💰 | Voice assistant (default) |
| `gemini-2.5-flash` | ⚡⚡ | ⭐⭐⭐ | 💰💰 | Complex reasoning |
| `gemini-2.5-flash-tts` | ⚡⚡ | ⭐⭐⭐ | 💰💰 | Voice with TTS output |

---

## Integrations

All integrations are **optional**. Leave settings empty to disable features you don't need.

### 🔍 Google Search

**Enables**: Web search for general knowledge questions

| Setting | Description | How to Get |
|---------|-------------|------------|
| `google_search_api_key` | Custom Search API key | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |
| `google_search_engine_id` | Programmable Search Engine ID | [Programmable Search](https://programmablesearchengine.google.com/) |

<details>
<summary><b>Setup Instructions</b></summary>

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Custom Search API"
4. Create API credentials (API Key)
5. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
6. Create a new search engine searching the entire web
7. Copy the Search Engine ID

</details>

---

### 🗺️ Google Maps

**Enables**: Travel time calculations with real-time traffic

| Setting | Description | How to Get |
|---------|-------------|------------|
| `google_maps_api_key` | Maps API key | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |

<details>
<summary><b>Setup Instructions</b></summary>

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Distance Matrix API"
3. Create API credentials (API Key)
4. Optionally restrict the key to Distance Matrix API only

</details>

---

### 📅 Google Calendar

**Enables**: Add events, list upcoming schedule

| Setting | Description | How to Get |
|---------|-------------|------------|
| `google_calendar_id` | Your calendar ID | Usually your email address, or found in Calendar Settings |

> **Note**: Requires GCP service account with Calendar API access. The service account email must be shared with your calendar.

---

### 🎵 Spotify

**Enables**: Play music by song, artist, album, or playlist name

| Setting | Description | How to Get |
|---------|-------------|------------|
| `spotify_client_id` | Application client ID | [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) |
| `spotify_client_secret` | Application client secret | Same as above |

**Requirements**:

- Spotcast integration installed in HA
- Spotify Premium account (for device control)

<details>
<summary><b>Setup Instructions</b></summary>

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Set Redirect URI to `http://localhost:8888/callback`
4. Copy Client ID and Client Secret
5. Install [Spotcast](https://github.com/fondberg/spotcast) in HA via HACS

</details>

---

### 🎬 Radarr (Movies)

**Enables**: Add movies, check library stats, view downloads

| Setting | Description | Example |
|---------|-------------|---------|
| `radarr_url` | Radarr server URL | `http://192.168.1.100:7878` |
| `radarr_api_key` | Radarr API key | Found in Settings → General |

**Commands**:

- "Add Dune Part 2 to Radarr"
- "What was the last movie downloaded?"
- "How many movies do I have?"
- "What movies are missing?"

---

### 📺 Sonarr (TV Shows)

**Enables**: Add series, check missing episodes, view downloads

| Setting | Description | Example |
|---------|-------------|---------|
| `sonarr_url` | Sonarr server URL | `http://192.168.1.100:8989` |
| `sonarr_api_key` | Sonarr API key | Found in Settings → General |

**Commands**:

- "Add The Mandalorian to Sonarr"
- "What episode was last downloaded?"
- "How many shows do I have?"
- "What episodes are missing?"

---

### 🔎 Prowlarr (Indexers)

**Enables**: Check indexer status and statistics

| Setting | Description | Example |
|---------|-------------|---------|
| `prowlarr_url` | Prowlarr server URL | `http://192.168.1.100:9696` |
| `prowlarr_api_key` | Prowlarr API key | Found in Settings → General |

---

### 📥 qBittorrent

**Enables**: Download speeds, active torrents, VPN status

| Setting | Description | Example |
|---------|-------------|---------|
| `qbittorrent_url` | qBittorrent Web UI URL | `http://192.168.1.100:8080` |
| `qbittorrent_username` | Web UI username | `admin` |
| `qbittorrent_password` | Web UI password | Your password |

**Commands**:

- "Is qBittorrent running?"
- "What's downloading?"
- "What's the download speed?"
- "Is the VPN connected?"

---

### 🌐 UniFi Controller (Advanced)

**Enables**: DHCP management, client queries, firewall rules, device status

| Setting | Description | Example |
|---------|-------------|---------|
| `unifi_controller_url` | Controller/Gateway URL | `https://192.168.1.1` |
| `unifi_controller_api_token` | API Token (preferred) | Generated in UniFi OS |
| `unifi_controller_username` | Admin username (fallback) | `admin` |
| `unifi_controller_password` | Admin password (fallback) | Your password |
| `unifi_site_id` | Site ID | `default` |

**To generate API Token**: UniFi OS → Settings → Admins & Users → Your User → API Tokens → Generate

**Commands**:

- "What's the next available IP on my IoT network?"
- "Show me active DHCP leases"
- "What devices are using the most bandwidth?"
- "List port forwarding rules"
- "What's my WAN IP?"
- "Show UniFi device status"

---

## Example Commands

### Smart Home

```
"Turn on the living room lights"
"Set the bedroom temperature to 21 degrees"
"What's the temperature in the office?"
"Turn it off" (remembers last controlled device)
"Is the garage door closed?"
"How long until the washing machine is done?"
"Where is Mike?"
```

### Media

```
"Play AC/DC"
"Play my Discover Weekly playlist"
"Add Inception to Radarr"
"What was the last movie downloaded?"
"How many TV shows are in Sonarr?"
```

### Information

```
"What's the weather in London?"
"Do I need an umbrella today?"
"How long to drive to Manchester?"
"What's the capital of France?"
"What's my fish tank temperature? Is that OK?"
```

### Camera

```
"What's on the garden camera?"
"Is anyone at the front door?"
```

### Memory

```
"Remember my favorite color is blue"
"What's my favorite color?"
"Remember my home address is 42 Oak Lane"
"What preferences do you have saved?"
"Forget my favorite color"
```

### Productivity

```
"What's my schedule for today?"
"Add meeting with John tomorrow at 2pm"
"Remind me to take out the bins when I get home"
"Set a timer for 10 minutes"
"What's the time?"
```

---

## Voice Pipeline Setup

For voice control, you need three components:

1. **Whisper (STT)** - Speech-to-Text
2. **Piper (TTS)** - Text-to-Speech  
3. **Wyoming Satellite** (optional) - Microphone/speaker device

### Setup Steps

1. Install **Whisper** add-on from HA Add-on Store
2. Install **Piper** add-on from HA Add-on Store
3. Go to **Settings → Voice assistants → Add Assistant**
4. Configure:
   - **Conversation agent**: Jarvis AI
   - **Speech-to-text**: Whisper
   - **Text-to-speech**: Piper (select your preferred voice)

### Jarvis Voice Model (Recommended)

For the authentic J.A.R.V.I.S. voice, install the custom Piper voice model:

1. **Download the voice model** from [HuggingFace](https://huggingface.co/jgkawell/jarvis/tree/main/en/en_GB/jarvis):
   - `jarvis-medium.onnx`
   - `jarvis-medium.onnx.json`

2. **Copy to Piper share folder**:

   ```bash
   scp jarvis-medium.onnx root@YOUR_HA_IP:/share/piper/
   scp jarvis-medium.onnx.json root@YOUR_HA_IP:/share/piper/
   ```

3. **Restart Piper add-on** to load the new voice

4. **Select Jarvis voice** in your Voice Assistant:
   - Settings → Voice assistants → Your Jarvis assistant
   - Text-to-speech → Voice: `jarvis-medium`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Wyoming Satellite (Optional)                 │
│                   (Raspberry Pi with mic/speaker)                │
│                              ↓ Audio                             │
├─────────────────────────────────────────────────────────────────┤
│                    Home Assistant Voice Pipeline                 │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────────┐   │
│  │   Whisper    │───▶│  Jarvis AI  │───▶│      Piper       │   │
│  │    (STT)     │    │  (This Addon)│    │      (TTS)       │   │
│  └──────────────┘    └──────┬──────┘    └──────────────────┘   │
├─────────────────────────────┼───────────────────────────────────┤
│                             │                                    │
│    ┌────────────────────────┼────────────────────────────────┐  │
│    │                    Jarvis Brain                          │  │
│    │  ┌─────────────────────┴─────────────────────────────┐  │  │
│    │  │              Gemini 2.0 Flash (LLM)                │  │  │
│    │  │           Function Calling & Reasoning             │  │  │
│    │  └─────────────────────┬─────────────────────────────┘  │  │
│    │                        │                                 │  │
│    │  ┌──────────────────┬──┴──┬──────────────────────────┐  │  │
│    │  │   Memory (SQLite) │     │     Tools & Functions    │  │  │
│    │  │   Preferences     │     │  - Home Assistant API    │  │  │
│    │  │   Context         │     │  - Spotify (Spotcast)    │  │  │
│    │  └──────────────────┘     │  - Radarr/Sonarr/Prowlarr │  │  │
│    │                           │  - qBittorrent            │  │  │
│    │                           │  - UniFi Controller       │  │  │
│    │                           │  - Google Search          │  │  │
│    │                           │  - Google Maps            │  │  │
│    │                           │  - Google Calendar        │  │  │
│    │                           │  - Weather (OpenMeteo)    │  │  │
│    │                           │  - Camera Vision          │  │  │
│    │                           └──────────────────────────┘  │  │
│    └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Add-on won't start

- **Check logs**: Settings → Add-ons → Jarvis AI → Log
- **Common cause**: Missing Gemini API key
- **Fix**: Add API key in Configuration tab, save, restart

### "I don't have that information"

- Jarvis uses web search for unknown topics
- Check Google Search API is configured
- Verify internet connectivity

### Entity not found

- Jarvis auto-resolves entity names
- Say "search for [device name]" to find correct entity ID
- Check entity exists in Home Assistant

### Spotify not playing

- Verify Spotcast integration is installed
- Check Spotify credentials are correct
- Ensure a Spotify device is active

### Slow responses

- Try a smaller Gemini model (`gemini-2.5-flash-lite`)
- Check your internet connection
- Optimize Whisper model size for faster STT

### Memory not persisting

- Memory is stored in `/data/jarvis_memory.db`
- Check the data directory exists and is writable
- Verify logs show "Memory system initialized"

---

## Privacy & Data

| Data Type | Storage Location | Details |
|-----------|------------------|---------|
| Preferences | `/data/jarvis_memory.db` | Local SQLite database, persists across restarts |
| Conversations | Not stored | Conversations are processed in real-time, not saved |
| API Calls | Google Gemini, Google APIs | Sent to Google for processing |
| Camera Images | Not stored | Analyzed in real-time, not saved |

**All data stays local** except for:

- Gemini API calls (conversation processing)
- Google Custom Search (web queries)
- Google Maps (travel time)
- Google Calendar (if configured)
- Spotify API (music search)
- *arr APIs (media management)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.3 | 2025-12-17 | Added custom icon, documentation overhaul |
| 1.0.2 | 2025-12-16 | UniFi Controller integration, camera analysis |
| 1.0.1 | 2025-12-15 | Google Calendar, location reminders |
| 1.0.0 | 2025-12-14 | Initial release |

---

## Credits

- **Inspiration**: Tony Stark's J.A.R.V.I.S. from Marvel's Iron Man
- **AI**: Google Gemini 2.0 Flash
- **Voice Pipeline**: Home Assistant Wyoming Protocol
- **TTS Voice**: Piper (custom Jarvis model optional)

---

## License

MIT License - Feel free to customize and extend!

---

**"At your service, sir. Always."** - J.A.R.V.I.S.
