from piper import PiperVoice
import wave
import io
import config

class Mouth:
    def __init__(self):
        self.model_path = "/app/piper_models/jarvis-high.onnx"
        self.config_path = "/app/piper_models/jarvis-high.onnx.json"
        # Note: paths are hardcoded for the Add-on environment (/app)
        try:
            self.voice = PiperVoice.load(self.model_path, self.config_path)
        except Exception as e:
            print(f"Error loading Piper model: {e}")
            self.voice = None

    def synthesize(self, text):
        """
        Synthesizes text to WAV bytes.
        """
        if not self.voice:
            return None
            
        try:
            with io.BytesIO() as wav_buffer:
                with wave.open(wav_buffer, "wb") as wav_file:
                    self.voice.synthesize_wav(text, wav_file)
                return wav_buffer.getvalue()
        except Exception as e:
            print(f"Error synthesizing text: {e}")
            return None

    def speak(self, text):
        # Legacy method for compatibility, but we won't use it in Wyoming
        pass
