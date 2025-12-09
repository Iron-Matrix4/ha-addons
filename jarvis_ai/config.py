import os
from dotenv import load_dotenv

load_dotenv()

# API Keys (Prioritize Env Vars for Add-on)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

# Check for missing keys
if not PICOVOICE_ACCESS_KEY:
    print("WARNING: PICOVOICE_ACCESS_KEY is not set.")

# Home Assistant
HA_URL = os.getenv("HA_URL", "http://supervisor/core") # Default to internal Add-on URL
HA_TOKEN = os.getenv("HASSIO_TOKEN") or os.getenv("HA_TOKEN")

# Spotify
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Configuration
WAKE_WORD = os.getenv("WAKE_WORD", "jarvis")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini") # "gemini" or "openai"
TTS_ENGINE = os.getenv("TTS_ENGINE", "piper") # "piper", "elevenlabs", "edge", "coqui"
STT_ENGINE = os.getenv("STT_ENGINE", "picovoice") # "picovoice", "google"

# Voice Settings (pyttsx3)
VOICE_ID = 0
VOICE_RATE = 170

# Voice Settings (ElevenLabs)
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM" # Rachel

# Voice Settings (Edge TTS)
EDGE_TTS_VOICE = "en-GB-RyanNeural"

# Voice Settings (Coqui TTS)
# Use /data for persistence in Add-ons or absolute path
COQUI_VOICE_PATH = os.getenv("COQUI_VOICE_PATH", "/app/jarvis_sample.mp3")

# Piper TTS Configuration
# Use /share or /data for models to avoid rebuilding image for model changes
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "/app/piper_models/jarvis-high.onnx")
PIPER_CONFIG_PATH = os.getenv("PIPER_CONFIG_PATH", "/app/piper_models/jarvis-high.onnx.json")
