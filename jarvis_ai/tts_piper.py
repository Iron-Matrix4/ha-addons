import subprocess
import config
import os

class Mouth:
    def speak(self, text):
        print(f"Jarvis (Piper): {text}")
        try:
            # Escape quotes
            safe_text = text.replace('"', '\\"')
            
            cmd = [
                "wsl", 
                "bash", 
                "/mnt/d/AntiGravity/Jarvis/run_piper_inference.sh",
                "--model", "/mnt/d/AntiGravity/Jarvis/piper_models/jarvis-high.onnx",
                "--config", "/mnt/d/AntiGravity/Jarvis/piper_models/jarvis-high.onnx.json",
                "--output", "/mnt/d/AntiGravity/Jarvis/jarvis_response.wav",
                "--text", safe_text
            ]
            
            # Run generation
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Play Audio (Windows)
            play_cmd = [
                "powershell", 
                "-c", 
                '(New-Object Media.SoundPlayer "d:\\AntiGravity\\Jarvis\\jarvis_response.wav").PlaySync()'
            ]
            subprocess.run(play_cmd, check=True)
            
        except Exception as e:
            print(f"Error in Piper TTS: {e}")
