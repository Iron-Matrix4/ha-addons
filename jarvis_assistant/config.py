import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
# API Keys
# It looks like you tried to paste the key directly. 
# If you want to use env vars, use os.getenv("GEMINI_API_KEY") and set it in your system.
# For now, I'll fix this to use the key you provided directly.
# API Keys
# It looks like you tried to paste the key directly. 
# If you want to use env vars, use os.getenv("GEMINI_API_KEY") and set it in your system.
# For now, I'll fix this to use the key you provided directly.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY", "")

# Debug Logging
if PICOVOICE_ACCESS_KEY:
    print(f"DEBUG: Loaded PICOVOICE_ACCESS_KEY: {PICOVOICE_ACCESS_KEY[:8]}...")
else:
    print("DEBUG: PICOVOICE_ACCESS_KEY is missing or empty!")

# Configuration
WAKE_WORD = "jarvis"
LLM_PROVIDER = "gemini" # or "openai"
TTS_ENGINE = "edge" # or "pyttsx3", "elevenlabs", "edge", "piper"
STT_ENGINE = "google" # or "whisper" (future)

# Voice Settings (pyttsx3)
VOICE_ID = 0 # Change index to select different voices
VOICE_RATE = 170

# Voice Settings (ElevenLabs)
# '21m00Tcm4TlvDq8ikWAM' is Rachel. 
# You need to find a "Jarvis" clone ID from the ElevenLabs library and paste it here.
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Voice Settings (Edge TTS)
# en-GB-RyanNeural is a good male voice.
# en-US-ChristopherNeural is another option.
EDGE_TTS_VOICE = "en-GB-RyanNeural"

# Voice Settings (Coqui TTS)
# Path to the reference audio file for cloning.
COQUI_VOICE_PATH = r"/app/jarvis_sample.mp3"

# Piper TTS Configuration
PIPER_MODEL_PATH = r"/app/piper_models/jarvis-high.onnx"
PIPER_CONFIG_PATH = r"/app/piper_models/jarvis-high.onnx.json"
