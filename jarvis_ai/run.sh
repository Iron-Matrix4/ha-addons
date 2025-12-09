#!/usr/bin/with-contenv bashio

echo "Starting Jarvis AI Add-on..."

# Export configuration options as environment variables
export PICOVOICE_ACCESS_KEY=$(bashio::config 'picovoice_access_key')
export GEMINI_API_KEY=$(bashio::config 'gemini_api_key')
export OPENAI_API_KEY=$(bashio::config 'openai_api_key')
export ELEVENLABS_API_KEY=$(bashio::config 'elevenlabs_api_key')
export WAKE_WORD=$(bashio::config 'wake_word')
export STT_ENGINE=$(bashio::config 'stt_engine')
export TTS_ENGINE=$(bashio::config 'tts_engine')

# Ensure audio device is available
if [ ! -e /dev/snd ]; then
    bashio::log.warning "No sound device found at /dev/snd. Audio features may not work."
fi

# Run the Python application
exec python3 Boot_Jarvis.py
