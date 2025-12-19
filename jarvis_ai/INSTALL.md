# Jarvis AI - Complete Installation Guide

This guide walks you through setting up Jarvis AI from scratch, including all optional integrations.

---

## What Am I Installing?

### Two Components Available

1. **Jarvis AI Add-on** (Required)
   - The conversation agent/brain
   - Runs inside Home Assistant
   - Enables voice control, all smart home features
   - **Everyone needs this**

2. **Jarvis Custom Integration** (Optional)
   - HTTP API for external access

- Only needed for: custom automations, HTTP control, external scripts
  - **Most users don't need this**

**This guide focuses on the add-on**. See [Custom Integration Setup](#custom-integration-optional) at the end if needed.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Core Configuration](#core-configuration)
4. [Voice Pipeline Setup](#voice-pipeline-setup)
5. [Optional Integrations](#optional-integrations)
6. [Verification](#verification)
7. [Wyoming Satellite Setup](#wyoming-satellite-setup-optional)

---

## Prerequisites

### Required

- ✅ Home Assistant (HA OS, Supervised, or Container)
- ✅ Google account for Gemini API

### Optional (for specific features)

| Feature | Requirement |
|---------|-------------|
| Voice control | Whisper + Piper add-ons |
| Music playback | Spotify Premium + Spotcast |
| Movie management | Radarr instance |
| TV management | Sonarr instance |
| Network queries | UniFi Controller |
| Wake word detection | Wyoming Satellite (e.g., Pi 5) |

---

## Installation

### Option A: One-Click Install (Recommended)

[![Add Repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FIron-Matrix4%2Fha-addons)

1. Click the button above to add the repository to Home Assistant
2. Go to **Settings → Add-ons → Add-on Store**
3. Find "Jarvis AI" in the list → Click **Install**
4. Continue to [Core Configuration](#core-configuration)

### Option B: Add Repository Manually

1. Go to **Settings → Add-ons → Add-on Store**
2. Click ⋮ (top right) → **Repositories**
3. Add: `https://github.com/Iron-Matrix4/ha-addons`
4. Click **Add** → **Close**
5. The repository will reload, find "Jarvis AI" → **Install**

### Option C: Local Install (Development)

If you want to install from local files (for development or modification):

1. **SSH into Home Assistant**

   ```bash
   ssh root@YOUR_HA_IP
   ```

2. **Create add-ons directory** (if it doesn't exist)

   ```bash
   mkdir -p /addons
   ```

3. **Copy the add-on** (from your machine)

   ```bash
   scp -r jarvis_ai root@YOUR_HA_IP:/addons/
   ```

4. **Set permissions**

   ```bash
   chmod +x /addons/jarvis_ai/run.sh
   ```

5. **Reload add-ons in HA**
   - Settings → Add-ons → Add-on Store
   - Click ⋮ (top right) → Reload
   - Find "Jarvis AI" in "Local add-ons" section

---

## Core Configuration

### Step 1: Set Up AI Provider (Choose One)

You need either a **Gemini API key** (free, simple) or **Vertex AI** (enterprise, more features).

#### Option A: Google AI Studio (Recommended for Personal Use)

This is the easiest setup - free tier available with generous limits.

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key
5. In Home Assistant, go to **Settings → Add-ons → Jarvis AI → Configuration**
6. Enter:

   ```yaml
   gemini_api_key: "YOUR_API_KEY_HERE"
   ```

7. Click **Save**

#### Option B: Google Vertex AI (Enterprise/Advanced)

Vertex AI offers higher rate limits, enterprise features, and access to the latest models. Requires a Google Cloud account with billing enabled.

1. **Create a GCP Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable billing (required, but free tier available)

2. **Enable Vertex AI API**
   - Go to **APIs & Services → Library**
   - Search for "Vertex AI API" → Enable

3. **Create Service Account**
   - Go to **IAM & Admin → Service Accounts**
   - Click **Create Service Account**
   - Name: `jarvis-ai`
   - Grant role: **Vertex AI User**
   - Click **Done**

4. **Generate JSON Key**
   - Click on your new service account
   - Go to **Keys** tab → **Add Key → Create new key**
   - Choose **JSON** → **Create**
   - Save the downloaded file

5. **Deploy Credentials to Home Assistant**

   ```bash
   scp your-credentials.json root@YOUR_HA_IP:/addon_configs/local_jarvis_ai/gcp-credentials.json
   ```

   Or place the file at `/data/gcp-credentials.json` inside the add-on container.

6. **Configure the Add-on**
   - Go to **Settings → Add-ons → Jarvis AI → Configuration**
   - Enter:

   ```yaml
   gcp_project_id: "your-project-id"
   ```

   > Leave `gemini_api_key` empty when using Vertex AI

7. Click **Save**

### Step 2: Choose Your Model (Optional)

| Model | Speed | Intelligence | Cost | Best For |
|-------|-------|--------------|------|----------|
| `gemini-2.5-flash-lite` | ⚡⚡⚡ | ⭐⭐ | 💰 | Voice assistant (default) |
| `gemini-2.5-flash` | ⚡⚡ | ⭐⭐⭐ | 💰💰 | Complex reasoning |
| `gemini-2.0-flash-exp` | ⚡⚡ | ⭐⭐⭐ | 💰💰 | Latest experimental |

To change the model:

```yaml
gemini_model: "gemini-2.5-flash"
```

### Step 3: Start the Add-on

1. Go to **Info** tab
2. Toggle **Start on boot** (recommended)
3. Click **Start**
4. Go to **Log** tab - you should see:

   ```
   J.A.R.V.I.S. - Just A Rather Very Intelligent System
   Starting Home Assistant Add-on...
   Jarvis conversation brain initialized with Gemini 2.0 Flash
   Jarvis conversation agent ready!
   ```

---

## Voice Pipeline Setup

To use voice control, you need Speech-to-Text and Text-to-Speech components.

### Step 1: Install Whisper (STT)

1. **Settings → Add-ons → Add-on Store**
2. Search for "Whisper" or "Faster Whisper"
3. Install and start
4. Recommended settings:

   ```yaml
   model: base
   language: en
   beam_size: 1
   ```

### Step 2: Install Piper (TTS)

1. **Settings → Add-ons → Add-on Store**
2. Search for "Piper"
3. Install and start

### Step 2.5: Install Jarvis Voice Model (Recommended)

For the authentic J.A.R.V.I.S. voice:

1. **Download the voice model** from [HuggingFace](https://huggingface.co/jgkawell/jarvis/tree/main/en/en_GB/jarvis):
   - Download `jarvis-medium.onnx`
   - Download `jarvis-medium.onnx.json`

2. **Copy files to Home Assistant**:

   ```bash
   scp jarvis-medium.onnx root@YOUR_HA_IP:/share/piper/
   scp jarvis-medium.onnx.json root@YOUR_HA_IP:/share/piper/
   ```

3. **Restart Piper add-on** to load the new voice

> **Note**: If you skip this step, you can use any default Piper voice (e.g., `en_GB-alan-medium`), but it won't sound like J.A.R.V.I.S.

### Step 3: Create Voice Assistant

1. Go to **Settings → Voice assistants**
2. Click **+ Add Assistant**
3. Configure:
   - **Name**: Jarvis
   - **Language**: English
   - **Conversation agent**: `Jarvis AI`
   - **Speech-to-text**: Whisper (or Faster Whisper)
   - **Text-to-speech**: Piper
4. Click **Create**

### Step 4: Test

1. Click the microphone icon in the HA sidebar
2. Say: "What time is it?"
3. Jarvis should respond!

---

## Optional Integrations

### Google Search (Web Knowledge)

**What it enables**: Answer general knowledge questions

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Go to **APIs & Services → Library**
4. Search for "Custom Search API" → Enable
5. Go to **APIs & Services → Credentials**
6. Click **+ Create Credentials → API Key**
7. Copy the API key

8. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
9. Click **Add** to create a new engine
10. For "Sites to search", select "Search the entire web"
11. Create and copy the **Search Engine ID**

12. Add to Jarvis configuration:

    ```yaml
    google_search_api_key: "YOUR_API_KEY"
    google_search_engine_id: "YOUR_ENGINE_ID"
    ```

---

### Google Maps (Travel Time)

**What it enables**: "How long to drive to work?"

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Distance Matrix API**
3. Create an API key (or reuse existing)
4. Add to configuration:

   ```yaml
   google_maps_api_key: "YOUR_API_KEY"
   ```

> **Tip**: Save your home/work addresses with Jarvis:
> "Remember my home is 42 Oak Lane"
> Then ask: "How long to get home?"

---

### Google Calendar

**What it enables**: "Add meeting at lunch today" / "What's on my calendar?" / "When was the last time I..."

1. **Create Service Account**:
   - Google Cloud Console → IAM & Admin → Service Accounts
   - Create new service account
   - Create JSON key → Download

2. **Enable Calendar API**:
   - APIs & Services → Library → Google Calendar API → Enable

3. **Share Calendar**:
   - Go to [Google Calendar](https://calendar.google.com/)
   - Settings → Your calendar → Share with specific people
   - Add your service account email (from the JSON file)
   - Give "Make changes to events" permission

4. **Get Calendar ID**:
   - Settings → Your calendar → Integrate calendar
   - Copy the Calendar ID (usually your email address)

5. **Deploy credentials file**:
   - Copy the JSON file to `/data/gcp-credentials.json` in the addon

6. **Add to configuration**:

   ```yaml
   google_calendar_id: "your.email@gmail.com"
   ```

**New Features (v1.3.1):**

```
"Add meeting at lunch today"         # Natural time: lunch, midday, dinner
"Remember my color is blue"           # Save custom color names
"Add dentist with my color"           # Use saved colors
"When was the last time I saw John?"  # Search past events
```

---

### Spotify

**What it enables**: "Play AC/DC" / "Play my Discover Weekly"

1. **Create Spotify App**:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Set Redirect URI: `http://localhost:8888/callback`
   - Copy Client ID and Client Secret

2. **Install Spotcast** (required):
   - Install HACS if not already
   - HACS → Integrations → Search "Spotcast" → Install
   - Restart HA
   - Configure Spotcast with your Spotify credentials

3. **Add to configuration**:

   ```yaml
   spotify_client_id: "YOUR_CLIENT_ID"
   spotify_client_secret: "YOUR_CLIENT_SECRET"
   ```

---

### Radarr

**What it enables**: "Add Dune to Radarr" / "What was the last movie downloaded?"

1. Open your Radarr web UI
2. Go to **Settings → General**
3. Copy your **API Key**
4. Add to configuration:

   ```yaml
   radarr_url: "http://192.168.1.100:7878"
   radarr_api_key: "YOUR_API_KEY"
   ```

---

### Sonarr

**What it enables**: "Add The Mandalorian" / "What's missing in Sonarr?"

1. Open your Sonarr web UI
2. Go to **Settings → General**
3. Copy your **API Key**
4. Add to configuration:

   ```yaml
   sonarr_url: "http://192.168.1.100:8989"
   sonarr_api_key: "YOUR_API_KEY"
   ```

---

### Prowlarr

**What it enables**: "How many indexers are working?"

1. Open your Prowlarr web UI
2. Go to Settings → General
3. Copy your API Key
4. Add to configuration:

   ```yaml
   prowlarr_url: "http://192.168.1.100:9696"
   prowlarr_api_key: "YOUR_API_KEY"
   ```

---

### qBittorrent

**What it enables**: "What's downloading?" / "Is the VPN connected?"

1. Enable qBittorrent Web UI:
   - qBittorrent → Tools → Options → Web UI
   - Enable Web UI
   - Set username/password
2. Add to configuration:

   ```yaml
   qbittorrent_url: "http://192.168.1.100:8080"
   qbittorrent_username: "admin"
   qbittorrent_password: "YOUR_PASSWORD"
   ```

---

### UniFi Controller (Advanced)

**What it enables**: DHCP queries, next available IP, bandwidth stats, firewall rules

1. **Generate API Token** (Preferred):
   - UniFi OS → Settings → Admins & Users
   - Click your user → API Tokens
   - Generate New Token → Copy

2. Add to configuration:

   ```yaml
   unifi_controller_url: "https://192.168.1.1"
   unifi_controller_api_token: "YOUR_TOKEN"
   unifi_site_id: "default"
   ```

   **Or use username/password** (fallback):

   ```yaml
   unifi_controller_url: "https://192.168.1.1"
   unifi_controller_username: "admin"
   unifi_controller_password: "YOUR_PASSWORD"
   unifi_site_id: "default"
   ```

---

## Verification

Test each integration after setup:

### Core

```
"What time is it?"
"Hello Jarvis"
```

### Home Assistant

```
"Turn on the living room light"
"What's the temperature?"
"Search for kitchen"
```

### Google Search

```
"What's the capital of France?"
"Who won the 2024 World Cup?"
```

### Weather

```
"What's the weather in London?"
"Do I need an umbrella?"
```

### Spotify

```
"Play Queen"
"Play my Daily Mix"
```

### Radarr/Sonarr

```
"What was the last movie downloaded?"
"How many TV shows do I have?"
```

### UniFi

```
"What's my WAN IP?"
"How many devices are connected?"
```

### Memory

```
"Remember my favorite food is pizza"
"What's my favorite food?"
```

---

## Wyoming Satellite Setup (Optional)

For wake word detection and dedicated microphone/speaker.

### Hardware Requirements

- Raspberry Pi 5 (or similar SBC)
- USB microphone or HAT
- Speaker (3.5mm or USB)

### Installation

1. **Flash Wyoming Satellite OS**:
   - Download from [Releases](https://github.com/rhasspy/wyoming-satellite/releases)
   - Flash to SD card with Balena Etcher

2. **Boot and Configure WiFi**:
   - Connect to `wyoming-satellite-XXXX` hotspot
   - Browse to `http://192.168.4.1`
   - Enter your WiFi credentials

3. **Configure Satellite**:

   ```yaml
   Home Assistant URL: http://YOUR_HA_IP:8123
   Access Token: (Long-lived token from HA)
   Wake Word: "jarvis"
   Voice Assistant: Jarvis (created earlier)
   ```

4. **Test**:
   - Say "Jarvis"
   - LED should light up
   - Say "Turn on the lights"
   - Response plays through speaker

---

## Next Steps

- **Customize**: Edit `tools.py` to add your own functions
- **Tune Memory**: Adjust context retention in `memory.py`
- **Multi-room**: Set up more Wyoming Satellites
- **Custom Voice**: Train a custom Jarvis voice for Piper

---

## Need Help?

1. Check **Logs**: Settings → Add-ons → Jarvis AI → Log
2. Review [README.md](README.md) for feature details
3. Check [Troubleshooting](README.md#troubleshooting) section

---

**Congratulations! J.A.R.V.I.S. is now online.**

*"At your service, sir. Always."*
