import edge_tts
import pygame
import asyncio
import os
import config

class Mouth:
    def __init__(self):
        self.voice = config.EDGE_TTS_VOICE
        # Initialize pygame mixer
        pygame.mixer.init()

    async def _speak_async(self, text):
        communicate = edge_tts.Communicate(text, self.voice)
        filename = "temp_audio.mp3"
        await communicate.save(filename)
        
        # Play audio
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            # Clean up
            pygame.mixer.music.unload()
            # Give it a moment to release the file handle
            await asyncio.sleep(0.1)
            try:
                os.remove(filename)
            except PermissionError:
                pass # Sometimes file is still locked, it will be overwritten next time anyway

    def speak(self, text):
        """
        Converts text to speech using Edge TTS.
        """
        print(f"Jarvis (Edge): {text}")
        try:
            asyncio.run(self._speak_async(text))
        except Exception as e:
            print(f"Error in Edge TTS: {e}")
