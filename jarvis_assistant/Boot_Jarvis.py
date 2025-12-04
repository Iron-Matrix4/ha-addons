import time
import random
import config
from stt import Ear
from llm import Brain

if config.TTS_ENGINE == "elevenlabs":
    from tts_elevenlabs import Mouth
elif config.TTS_ENGINE == "edge":
    from tts_edge import Mouth
elif config.TTS_ENGINE == "coqui":
    from tts_coqui import Mouth
elif config.TTS_ENGINE == "piper":
    from tts_piper import Mouth
else:
    from tts import Mouth

from wake_word import WakeWord

def main():
    print("Initializing J.A.R.V.I.S...")
    ear = Ear()
    mouth = Mouth()
    brain = Brain()
    wake_word = WakeWord()
    
    mouth.speak("Jarvis is online. How may I help you, Sir?")

    continue_conversation = False
    retry_count = 0

    while True:
        # 1. Wait for "Jarvis" (Instant) OR Continue Conversation
        if continue_conversation or wake_word.listen():
            
            if not continue_conversation:
                print("Wake word detected.")
                retry_count = 0
            else:
                print("Continuing conversation...")

            # 2. Listen for actual command (Google STT)
            print("Listening for command...")
            text = ear.listen()
            
            if text:
                retry_count = 0 # Reset on success
                command = text
                
                if "goodbye" in command or "shut down" in command:
                    mouth.speak("Powering down. Goodbye, Sir.")
                    break
                
                response = brain.process(command)
                mouth.speak(response)
                
                # Check if we should keep listening
                if response.strip().endswith("?") or "anything else" in response.lower():
                    continue_conversation = True
                else:
                    continue_conversation = False
            else:
                # If we were in a conversation and heard nothing, try again once
                if continue_conversation:
                    if retry_count < 1:
                        errors = [
                            "I didn't catch that, Sir.",
                            "Could you repeat that?",
                            "I'm afraid I missed that.",
                            "Pardon me, Sir?",
                            "My apologies, I didn't hear you."
                        ]
                        mouth.speak(random.choice(errors))
                        retry_count += 1
                        # Loop will continue and skip wake word because continue_conversation is still True
                    else:
                        continue_conversation = False
                        retry_count = 0
                        # mouth.speak("I'm listening whenever you need me, Sir.")
                pass

if __name__ == "__main__":
    main()
