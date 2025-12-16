# Jarvis AI - Home Assistant Conversation Agent

**J.A.R.V.I.S.** - Just A Rather Very Intelligent System

An intelligent conversation agent for Home Assistant powered by Google Gemini 2.0 Flash, featuring persistent memory, natural language control, and integration with Spotify, Radarr, and Sonarr.

## Features

### 🎯 Core Capabilities

- **Natural Language Understanding** - Powered by Gemini 2.0 Flash with function calling
- **Persistent Memory** - Remembers your preferences and learned context
- **Smart Entity Resolution** - Auto-corrects entity names and handles vague commands
- **Contextual Knowledge** - Combines live HA states with web knowledge

### 🏠 Home Assistant Integration

- **Full HA Control** - Lights, climate, switches, and all entities
- **Wyoming Protocol** - Native integration with HA's voice pipeline
- **Smart Follow-ups** - "Turn it off" knows what "it" refers to
- **Complex Logic** - Conditional actions based on current states

### 🎵 Media & Entertainment

- **Spotify Control** - Play songs, artists, albums, or playlists
- **Radarr Integration** - Add and search for movies
- **Sonarr Integration** - Add and search for TV series

### 🌐 Knowledge & Search

- **Web Search** - Answers general knowledge questions
- **Weather Information** - Current weather for any city
- **Contextual Answers** - Combines HA states with web knowledge

### 🤖 Witty Personality

- Responds like Tony Stark's J.A.R.V.I.S.
- Helpful, polite, and slightly sarcastic
- Natural conversational style

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

### Quick Start

1. Copy this folder to `/addons/jarvis_ai` on your Home Assistant instance
2. Reload add-ons in HA
3. Install "Jarvis AI Conversation Agent"
4. Configure your Gemini API key
5. Start the add-on
6. Configure voice pipeline in HA

## Configuration

### Required Settings

| Option | Description |
|--------|-------------|
| `gemini_api_key` | Google Gemini API key (required) |

### Optional Settings

| Option | Description |
|--------|-------------|
| `spotify_client_id` | Spotify API client ID |
| `spotify_client_secret` | Spotify API client secret |
| `radarr_url` | Radarr server URL (e.g., `http://192.168.1.100:7878`) |
| `radarr_api_key` | Radarr API key |
| `sonarr_url` | Sonarr server URL (e.g., `http://192.168.1.100:8989`) |
| `sonarr_api_key` | Sonarr API key |

## Voice Pipeline Setup

1. Install required add-ons:
   - **Piper** - For TTS (use your custom Jarvis voice)
   - **Faster-Whisper** or **Whisper** - For STT
   - **Wyoming Satellite** - On your Pi 5 for wake word detection

2. Create a voice assistant in HA:
   - Go to **Settings** → **Voice assistants**
   - Click **Add Assistant**
   - Set **Conversation agent** to "Jarvis AI"
   - Set **Speech-to-text** to your Whisper add-on
   - Set **Text-to-speech** to your Piper add-on
   - Save

3. Configure Wyoming Satellite (Pi 5):
   - Point it to your HA instance
   - Select the voice assistant you just created

## Example Commands

### Home Assistant Control

```
"Turn on the office light"
"What's the temperature in the bedroom?"
"Set the living room heating to 21 degrees"
"Is the fish tank temperature OK?" (gets temp + searches ideal range)
```

### Music & Media

```
"Play AC/DC"
"Play my Discover Weekly playlist"
"Add Dune Part 2 to Radarr"
"Search for The Mandalorian on Sonarr"
```

### Knowledge & Information

```
"What's the weather in London?"
"What's the population of Asia?"
"Set a timer for 10 minutes"
```

### Memory & Preferences

```
"Remember I prefer Celsius without saying the unit"
"What temperature unit do I prefer?"
```

### Smart Follow-ups

```
You: "Turn on the office light"
Jarvis: "Office lighting, online sir"
You: "Turn it off"
Jarvis: "Turning off office light" (knows you mean office light)
```

## Logging

View logs in Home Assistant:

- **Settings** → **Add-ons** → **Jarvis AI** → **Log**

## Troubleshooting

### Add-on won't start

- Check that Gemini API key is configured
- View logs for specific error messages

### "I don't have that information"

- Jarvis defaults to web search for unknowns
- Check internet connectivity

### Entity not found errors

- Jarvis will try to auto-resolve entity names
- Check entity IDs in Home Assistant

### Spotify not working

- Ensure Spotify credentials are configured
- Check that `media_player.spotify_luke` exists (or update entity_id in code)

## Architecture

```
Wyoming Satellite (Pi 5)
    ↓ (Wake word + Audio)
Home Assistant Voice Pipeline
    ↓ (STT via Whisper)
Jarvis Conversation Agent (This Add-on)
    ├─ Gemini 2.0 Flash (Brain)
    ├─ Persistent Memory (SQLite)
    └─ Tools (HA, Spotify, Radarr, Sonarr, Search)
    ↓ (Text response)
Piper TTS (Jarvis Voice)
    ↓ (Audio output)
Wyoming Satellite Speaker
```

## Privacy & Data

- **Memory Database**: Stored locally in `/data/jarvis_memory.db` (persists across restarts)
- **API Calls**: Gemini API (Google), Spotify API, DuckDuckGo search
- **No External Storage**: All conversations and preferences stay local

## Credits

- **Inspiration**: Tony Stark's J.A.R.V.I.S. from Marvel's Iron Man
- **AI**: Google Gemini 2.0 Flash
- **Voice Pipeline**: Home Assistant Wyoming Protocol

## License

MIT License - Feel free to customize and extend!

## Support

For issues or questions, please check the logs first, then open an issue on GitHub.

---

**"At your service, sir. Always."** - J.A.R.V.I.S.
