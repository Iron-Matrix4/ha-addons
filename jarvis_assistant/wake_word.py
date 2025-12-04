import pvporcupine
import struct
import config
import sys

class WakeWord:
    def __init__(self, use_mic=True):
        try:
            self.porcupine = pvporcupine.create(
                access_key=config.PICOVOICE_ACCESS_KEY,
                keywords=['jarvis']
            )
            self.frame_length = self.porcupine.frame_length
            self.sample_rate = self.porcupine.sample_rate
            
            if use_mic:
                import pyaudio
                self.pa = pyaudio.PyAudio()
                self.audio_stream = self.pa.open(
                    rate=self.porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=self.porcupine.frame_length
                )
            else:
                self.pa = None
                self.audio_stream = None
                
        except Exception as e:
            print(f"Error initializing Porcupine: {e}")
            raise e

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
