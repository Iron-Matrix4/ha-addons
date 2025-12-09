import pvcheetah
import pyaudio
import struct
import config
import os

class Ear:
    def __init__(self):
        try:
            self.cheetah = pvcheetah.create(access_key=config.PICOVOICE_ACCESS_KEY)
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.cheetah.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.cheetah.frame_length
            )
            print("Picovoice STT (Cheetah) Initialized.")
        except Exception as e:
            print(f"Error initializing Cheetah STT: {e}")
            self.cheetah = None

    def listen(self):
        """
        Listens for audio input and converts it to text using Picovoice Cheetah.
        Returns:
            str: The recognized text, or None if unintelligible/timeout.
        """
        if not self.cheetah:
            print("Cheetah STT not available.")
            return None

        print("Listening (Picovoice)...")
        transcript = ""
        is_endpoint = False
        
        # Simple loop to capture audio until endpoint (silence) is detected
        # You might want to implement a max timeout here to prevent infinite loops
        try:
            while not is_endpoint:
                pcm = self.audio_stream.read(self.cheetah.frame_length)
                pcm = struct.unpack_from("h" * self.cheetah.frame_length, pcm)
                
                partial_transcript, is_endpoint = self.cheetah.process(pcm)
                transcript += partial_transcript
                
            # One final flush to get any remaining text
            final_transcript = self.cheetah.flush()
            transcript += final_transcript
            
            print(f"Heard: {transcript}")
            return transcript.lower() if transcript else None
            
        except Exception as e:
            print(f"Error during listening: {e}")
            return None

    def cleanup(self):
        if self.cheetah:
            self.cheetah.delete()
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pa:
            self.pa.terminate()
