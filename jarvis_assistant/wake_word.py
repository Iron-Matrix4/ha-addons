import pvporcupine
import struct
import config
import sys

class WakeWord:
    def __init__(self, use_mic=True):
        self.porcupine = None
        
        # Debug info
        try:
            import platform
            print(f"Platform: {platform.system()} {platform.release()} {platform.machine()}")
            try:
                print(f"Picovoice Available Keywords: {list(pvporcupine.KEYWORDS)}")
            except:
                pass
        except:
            pass

        # Try keywords in order preference
        attempts = ['jarvis', 'porcupine']
        
        for kw in attempts:
            try:
                print(f"Attempting to initialize Porcupine with keyword: '{kw}'")
                self.porcupine = pvporcupine.create(
                    access_key=config.PICOVOICE_ACCESS_KEY,
                    keywords=[kw]
                )
                print(f"Successfully initialized with keyword: '{kw}'")
                break
            except Exception as e:
                print(f"Failed to init '{kw}': {e}")
        
        if self.porcupine is None:
            print("CRITICAL: Failed to initialize Porcupine with any keywords.")
            sys.exit(1)

        self.frame_length = self.porcupine.frame_length
        self.sample_rate = self.porcupine.sample_rate
        
        if use_mic:
            try:
                import pyaudio
                self.pa = pyaudio.PyAudio()
                self.audio_stream = self.pa.open(
                    rate=self.porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=self.porcupine.frame_length
                )
            except Exception as e:
                print(f"Microphone init failed (expected in Docker if passing stream): {e}")
                self.pa = None
                self.audio_stream = None
        else:
            self.pa = None
            self.audio_stream = None

    def process(self, pcm):
        """
        Processes a single chunk of audio (must be correct length).
        Returns True if wake word detected.
        """
        keyword_index = self.porcupine.process(pcm)
        return keyword_index >= 0

    def listen(self):
        """
        Blocks until the wake word is detected (Mic mode only).
        """
        if not self.audio_stream:
            raise RuntimeError("Microphone not initialized")
            
        print("Waiting for wake word...")
        while True:
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            if self.process(pcm):
                print("Wake word detected!")
                return True

    def cleanup(self):
        if self.audio_stream:
            self.audio_stream.close()
        if self.pa:
            self.pa.terminate()
        if self.porcupine:
            self.porcupine.delete()
