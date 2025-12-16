# Jarvis AI - Installation Guide

Complete step-by-step instructions for installing and configuring Jarvis AI on your Home Assistant instance.

## Prerequisites

### Required

- ✅ Home Assistant instance (HA OS, Supervised, or Container)
- ✅ Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- ✅ SSH or direct file access to your HA instance

### Optional (for full features)

- Spotify Developer Account ([Create app here](https://developer.spotify.com/dashboard))
- Radarr instance for movie management
- Sonarr instance for TV series management
- Raspberry Pi 5 (or similar) for Wyoming Satellite

---

## Part 1: Install the Add-on

### Option A: Via SSH (Recommended)

1. **SSH into your Home Assistant instance:**

   ```bash
   ssh root@your-ha-ip
   ```

   > **Note**: Use your HA root password (NOT your HA web UI password!)

2. **Navigate to add-ons directory:**

   ```bash
   cd /addons
   ```

   > If `/addons` doesn't exist, create it:
>
   > ```bash
   > mkdir -p /addons
   > ```

3. **Copy the Jarvis add-on folder:**

   From your Windows machine where the files are located:

   ```powershell
   # On your Windows machine (PowerShell)
   scp -r "d:\AntiGravity\AG2\ha-addons\jarvis_ai" root@YOUR_HA_IP:/addons/
   ```

   Replace `YOUR_HA_IP` with your Home Assistant IP address.

4. **Verify files are copied:**

   ```bash
   ls /addons/jarvis_ai
   ```

   You should see:

   ```
   config.yaml
   Dockerfile
   README.md
   INSTALL.md
   run.sh
   requirements.txt
   main.py
   conversation.py
   wyoming_handler.py
   memory.py
   tools.py
   config_helper.py
   ```

5. **Set permissions:**

   ```bash
   chmod +x /addons/jarvis_ai/run.sh
   ```

### Option B: Via Home Assistant File Editor

1. Install "File Editor" add-on from the official add-on store
2. Use File Editor to create `/addons/jarvis_ai/` folder
3. Copy each file from your `d:\AntiGravity\AG2\ha-addons\jarvis_ai\` folder
4. Make sure all `.py` files and `.sh` files are copied correctly

---

## Part 2: Install & Configure the Add-on

1. **Reload Add-ons:**
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click the ⋮ menu (top right) → **Reload**
   - Wait a few seconds

2. **Find Jarvis AI:**
   - Scroll down to " Local add-ons" section
   - You should see "Jarvis AI Conversation Agent"
   - Click on it

3. **Install:**
   - Click **Install**
   - Wait for installation to complete (may take 2-5 minutes)

4. **Configure:**
   - Go to the **Configuration** tab
   - Enter your **Gemini API Key** (required)

   **Optional configurations:**

   ```yaml
   gemini_api_key: "YOUR_GEMINI_API_KEY_HERE"
   spotify_client_id: "YOUR_SPOTIFY_CLIENT_ID"          # Optional
   spotify_client_secret: "YOUR_SPOTIFY_CLIENT_SECRET"  # Optional
   radarr_url: "http://192.168.1.100:7878"              # Optional
   radarr_api_key: "YOUR_RADARR_API_KEY"                # Optional
   sonarr_url: "http://192.168.1.100:8989"              # Optional
   sonarr_api_key: "YOUR_SONARR_API_KEY"                # Optional
   ```

5. **Save Configuration:**
   - Click **Save**

6. **Start the Add-on:**
   - Go to the **Info** tab
   - Toggle **Start on boot** (recommended)
   - Click **Start**

7. **Check Logs:**
   - Go to the **Log** tab
   - You should see:

     ```
     J.A.R.V.I.S. - Just A Rather Very Intelligent System
     Starting Home Assistant Add-on...
     Jarvis conversation brain initialized with Gemini 2.0 Flash
     Jarvis conversation agent ready!
     Waiting for connections from Home Assistant...
     ```

---

## Part 3: Set Up Voice Pipeline

### A. Install Required Add-ons

1. **Install Piper (TTS):**
   - **Settings** → **Add-ons** → **Add-on Store**
   - Search for "Piper"
   - Install **Piper TTS**
   - Configure with your custom Jarvis ONNX files:

     ```
     Voice model: /share/piper/jarvis-high.onnx
     ```

   - Start the add-on

2. **Install Faster-Whisper (STT):**
   - **Settings** → **Add-ons** → **Add-on Store**
   - Search for "Whisper"
   - Install **Faster-Whisper**
   - Configuration (recommended):

     ```yaml
     model: medium
     language: en
     ```

   - Start the add-on

### B. Copy Piper Voice Model

1. **Copy your Jarvis ONNX files to HA:**

   ```powershell
   # From Windows
   scp "d:\AntiGravity\Jarvis\piper_models\jarvis-high.onnx" root@YOUR_HA_IP:/share/piper/
   scp "d:\AntiGravity\Jarvis\piper_models\jarvis-high.onnx.json" root@YOUR_HA_IP:/share/piper/
   ```

2. **Restart Piper add-on** to load the new voice

### C. Create Voice Assistant in HA

1. **Go to Voice Assistants:**
   - **Settings** → **Voice assistants**

2. **Add Assistant:**
   - Click **+ Add Assistant**

3. **Configure:**
   - **Name**: `Jarvis`
   - **Language**: `English`
   - **Conversation agent**: Select `conversation.jarvis_ai`
   - **Speech-to-text**: Select `faster_whisper`
   - **Text-to-speech**: Select `tts.piper` with `jarvis-high` voice
   - Click **Create**

4. **Test in HA:**
   - Click the microphone icon in HA's UI
   - Say: "What's the time?"
   - Jarvis should respond!

---

## Part 4: Set Up Wyoming Satellite (Pi 5)

### A. Flash Wyoming Satellite to Pi 5

1. **Download Wyoming Satellite OS:**
   - [Wyoming Satellite Releases](https://github.com/rhasspy/wyoming-satellite/releases)
   - Download the image for Raspberry Pi (`.img.xz` file)

2. **Flash to SD Card:**
   - Use [Balena Etcher](https://www.balena.io/etcher/) or [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
   - Flash the image to a 16GB+ microSD card

3. **Boot Pi 5:**
   - Insert SD card
   - Connect power, microphone, and speaker
   - Wait for boot (LED will blink)

### B. Configure Wyoming Satellite

1. **Connect to WiFi:**
   - The Pi will create a WiFi hotspot named `wyoming-satellite-XXXX`
   - Connect to it with your phone/laptop
   - Open browser to `http://192.168.4.1`
   - Configure your WiFi credentials

2. **Configure Satellite:**
   - After WiFi setup, find the Pi's IP on your network
   - Browse to `http://PI_IP`
   - Configure:

     ```
     Home Assistant URL: http://YOUR_HA_IP:8123
     Access Token: (Generate a Long-Lived Access Token in HA)
     Wake Word: Jarvis (or use Picovoice with "jarvis" model)
     Voice Assistant: Jarvis (the one you created in Part 3)
     ```

3. **Test Wake Word:**
   - Say "Jarvis"
   - LED should light up
   - Say "Turn on the office light"
   - Jarvis should respond through the speaker!

---

## Part 5: Get API Keys (Optional Services)

### Spotify API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **Create App**
4. Fill in:
   - **App Name**: Jarvis
   - **App Description**: Home Assistant voice control
   - **Redirect URI**: `http://localhost:8888/callback`
5. Save
6. Copy **Client ID** and **Client Secret**
7. Add to Jarvis add-on configuration

### Radarr API

1. Open Radarr web UI
2. **Settings** → **General**
3. Copy **API Key**
4. Add to Jarvis: `radarr_url: http://YOUR_RADARR_IP:7878` and `radarr_api_key: YOUR_KEY`

### Sonarr API

1. Open Sonarr web UI
2. **Settings** → **General**
3. Copy **API Key**
4. Add to Jarvis: `sonarr_url: http://YOUR_SONARR_IP:8989` and `sonarr_api_key: YOUR_KEY`

---

## Verification

### Test Basic Functionality

1. **Home Assistant Control:**

   ```
   Say: "Jarvis, turn on the office light"
   Expected: Light turns on + "Office lighting, online sir"
   ```

2. **Temperature Query:**

   ```
   Say: "What's the temperature in the bedroom?"
   Expected: "The bedroom temperature is 20 degrees" (or similar)
   ```

3. **Web Search:**

   ```
   Say: "What's the capital of France?"
   Expected: "Paris, sir" (or expanded answer)
   ```

4. **Memory:**

   ```
   Say: "Remember my favorite color is blue"
   Expected: "Noted, sir"
   
   Later: "What's my favorite color?"
   Expected: "Your favorite color is blue, sir"
   ```

5. **Spotify (if configured):**

   ```
   Say: "Play AC/DC"
   Expected: Music starts playing
   ```

---

## Troubleshooting

### Add-on won't start

- **Check logs**: Settings → Add-ons → Jarvis AI → Log tab
- **Common issue**: Missing Gemini API key
- **Fix**: Add API key in Configuration tab and restart

### "Connection refused" errors

- **Issue**: Wyoming server not accessible
- **Check**: Port 10400 is exposed in config.yaml
- **Verify**: Add-on is running (Info tab shows "Running")

### Gemini function calling not working

- **Check**: Internet connectivity from HA instance
- **Verify**: Gemini API key is valid
- **Test**: Try a simple question like "What's 2+2?"

### Spotify playback fails

- **Check**: Spotify is installed and logged in
- **Verify**: `media_player.spotify_luke` exists (or update entity_id in tools.py)
- **Fix**: Open Spotify app on your device first

### Memory not persisting

- **Check**: `/data` directory exists and is writable
- **Verify**: Logs show "Memory system initialized at /data/jarvis_memory.db"
- **Fix**: Restart add-on if database got corrupted

---

## Next Steps

- **Customize**: Edit `tools.py` to add your own functions
- **Tune Memory**: Adjust context retention in `memory.py`
- **Add Wake Words**: Configure additional wake words in Wyoming Satellite
- **Multi-room**: Set up more Wyoming Satellites for other rooms

---

## Need Help?

1. Check the **Logs** tab in the add-on
2. Review this installation guide
3. Check [README.md](README.md) for command examples
4. Open an issue on GitHub with logs attached

---

**Congratulations! J.A.R.V.I.S. is now online. At your service, sir. Always.**
