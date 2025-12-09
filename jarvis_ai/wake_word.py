import pvporcupine
import pyaudio
import struct
import config
import sys

class WakeWord:
    def __init__(self):
        try:
            self.porcupine = pvporcupine.create(
                access_key=config.PICOVOICE_ACCESS_KEY,
                keywords=[config.WAKE_WORD]
            )
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
        except Exception as e:
            print(f"Error initializing Porcupine: {e}")
            sys.exit(1)

    def listen(self):
        """
        Blocks until the wake word is detected.
        """
        print("Waiting for wake word...")
        while True:
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                print("Wake word detected!")
                return True

    def cleanup(self):
        if self.audio_stream:
            self.audio_stream.close()
        if self.pa:
            self.pa.terminate()
        if self.porcupine:
            self.porcupine.delete()
