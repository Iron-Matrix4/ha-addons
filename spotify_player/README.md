# Spotify Player Add-on for Home Assistant

Keep a Spotify session always active on your Home Assistant server using spotifyd.

## What This Does

This add-on runs **spotifyd** - a lightweight Spotify Connect client that:

- Creates a Spotify Connect device called "Home Assistant" (or your custom name)
- Keeps the Spotify session active 24/7
- Enables voice control via Jarvis without needing external devices
- Uses minimal resources (~20MB RAM)

## Installation

1. **Add this repository** to your Home Assistant:
   - Settings → Add-ons → Add-on Store → ⋮ → Repositories
   - Add: `https://github.com/Iron-Matrix4/ha-addons` (or local path)

2. **Install the add-on:**
   - Find "Spotify Player (spotifyd)" in the store
   - Click Install

3. **Configure:**
   - Go to Configuration tab
   - Enter your **Spotify username** (email)
   - Enter your **Spotify password**
   - (Optional) Change device name (default: "Home Assistant")
   - (Optional) Change bitrate (default: 320 kbps)

4. **Start the add-on:**
   - Go to Info tab
   - Click Start
   - Enable "Start on boot" if you want it always running

## Usage

Once running, you'll see a new Spotify device called "Home Assistant" (or your custom name) in:

- Spotify app on phone/PC → Devices list
- `media_player.spotify_luke` → source_list in Home Assistant

**With Jarvis:**

- "Play Queen" → Jarvis will ask which device, say "Home Assistant"
- "Play music on Office Display" → Uses the active session to cast
- "What's playing?" → Gets current track info

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `spotify_username` | Your Spotify email address | (required) |
| `spotify_password` | Your Spotify password | (required) |
| `device_name` | Name shown in Spotify devices | "Home Assistant" |
| `bitrate` | Audio quality (96/160/320 kbps) | 320 |

## Requirements

- **Spotify Premium account** (Spotify Connect requires Premium)
- Home Assistant OS or Supervised
- ~20MB RAM
- Audio support (provided by PulseAudio in container)

## Troubleshooting

**"Device not showing in Spotify"**

- Check logs for authentication errors
- Verify username/password are correct
- Make sure you have Spotify Premium

**"Connection errors"**

- Restart the add-on
- Check Home Assistant has internet access
- Verify no firewall blocking Spotify

**"Jarvis can't find the session"**

- Restart both Spotify Player and Jarvis add-ons
- Wait 10 seconds for Spotify to register the device
- Try: "Play music on Home Assistant"

## How It Works

```
spotifyd → Spotify Servers → Creates "Home Assistant" device
                ↓
    Jarvis sees active Spotify session
                ↓
    Can play music / control playback
```

The add-on doesn't need to actually play audio - it just needs to exist as a Spotify Connect device to keep the session active!

## Support

- Issues: [GitHub Issues](https://github.com/Iron-Matrix4/ha-addons/issues)
- Jarvis Integration: See Jarvis add-on documentation
- spotifyd: <https://github.com/Spotifyd/spotifyd>
