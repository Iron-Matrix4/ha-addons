import speech_recognition as sr
import config

class Ear:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with self.microphone as source:
            print("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source)

    def listen(self):
        """
        Listens for audio input and converts it to text.
        Returns:
            str: The recognized text, or None if unintelligible.
        """
        with self.microphone as source:
            print("Listening...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("Recognizing...")
                text = self.recognizer.recognize_google(audio)
                print(f"Heard: {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return None
