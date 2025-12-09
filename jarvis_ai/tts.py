import pyttsx3
import config

class Mouth:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.set_voice()

    def set_voice(self):
        voices = self.engine.getProperty('voices')
        # Try to find a good English voice
        # On Windows, usually Zira (female) or David (male) are available.
        # We can try to select one based on config.
        try:
            self.engine.setProperty('voice', voices[config.VOICE_ID].id)
        except IndexError:
            pass # Fallback to default
        
        self.engine.setProperty('rate', config.VOICE_RATE)

    def speak(self, text):
        """
        Converts text to speech.
        """
        print(f"Jarvis: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
