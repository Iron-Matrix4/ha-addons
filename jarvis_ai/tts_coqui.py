import soundfile as sf
import torch
import torchaudio

# Monkey-patch torchaudio.load to use soundfile directly
# This bypasses the TorchCodec requirement in the nightly build
def my_load(filepath, **kwargs):
    data, samplerate = sf.read(filepath)
    tensor = torch.from_numpy(data).float()
    if tensor.ndim == 1:
        tensor = tensor.unsqueeze(0)
    else:
        tensor = tensor.t()
    return tensor, samplerate

torchaudio.load = my_load

from TTS.api import TTS
import pygame
import os
import config
import time

# import torch_directml (Removed)
from rvc_module import VoiceConverter

class Mouth:
    def __init__(self):
        # Restoring CUDA support for RTX 5090 (Nightly Build)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Initializing Coqui TTS on {self.device}...")
        
        try:
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        except Exception as e:
            print(f"Failed to init on {self.device}: {e}")
            if self.device == "cuda":
                print("Falling back to CPU...")
                self.device = "cpu"
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
        
        self.reference_audio = config.COQUI_VOICE_PATH
        if not os.path.exists(self.reference_audio):
            print(f"Warning: Reference audio file not found at {self.reference_audio}")
            
        # Initialize RVC
        self.rvc = VoiceConverter()
        
        pygame.mixer.init()

    def speak(self, text):
        print(f"Jarvis (Coqui): {text}")
        output_path = "temp_output.wav"
        rvc_output_path = "temp_output_rvc.wav"
        
        try:
            # Generate speech to file
            with torch.no_grad():
                self.tts.tts_to_file(text=text, speaker_wav=self.reference_audio, language="en", file_path=output_path)
            
            # Apply RVC Conversion
            final_path = self.rvc.convert(output_path, rvc_output_path)
            
            # Play audio
            pygame.mixer.music.load(final_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
            time.sleep(0.1)
            
            # Cleanup
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                if os.path.exists(rvc_output_path):
                    os.remove(rvc_output_path)
            except PermissionError:
                pass
            
        except Exception as e:
            print(f"Error in Coqui TTS: {e}")
            if self.device != "cpu":
                print("Acceleration error detected. Switching to CPU for future requests...")
                self.device = "cpu"
                self.tts = self.tts.to("cpu")
                # Retry once on CPU
                try:
                    self.speak(text)
                except Exception as retry_e:
                    print(f"Retry failed: {retry_e}")
