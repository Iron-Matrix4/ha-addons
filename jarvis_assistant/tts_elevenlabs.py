from elevenlabs.client import ElevenLabs
from elevenlabs import play
import config

class Mouth:
    def __init__(self):
        if not config.ELEVENLABS_API_KEY:
            print("Warning: ELEVENLABS_API_KEY not set.")
            self.client = None
        else:
            self.client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
        
        # "Paul Bettany" style voice ID (This is a placeholder, user needs to find a specific clone or use a similar pre-made one)
        # '21m00Tcm4TlvDq8ikWAM' is "Rachel", a default. 
        # We will use a variable so it can be changed.
        self.voice_id = config.ELEVENLABS_VOICE_ID 

    def speak(self, text):
        """
        Converts text to speech using ElevenLabs.
        """
        if not self.client:
            print("ElevenLabs not initialized. Text:", text)
            return

        print(f"Jarvis (ElevenLabs): {text}")
        try:
            audio = self.client.generate(
                text=text,
                voice=self.voice_id,
                model="eleven_monolingual_v1"
            )
            play(audio)
        except Exception as e:
            print(f"Error generating audio: {e}")
