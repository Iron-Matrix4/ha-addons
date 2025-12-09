import os
from dotenv import load_dotenv
load_dotenv()
import tools
import config

def test_music():
    print("Testing Music Tool...")
    print(f"DEBUG: Client ID from config: {config.SPOTIPY_CLIENT_ID}")
    print(f"DEBUG: Client ID from os: {os.getenv('SPOTIPY_CLIENT_ID')}")
    
    if not config.SPOTIPY_CLIENT_ID:
        print("Skipping test: No Spotify Credentials")
        return

    # Try to play a song
    print(tools.play_music("Bohemian Rhapsody"))

if __name__ == "__main__":
    test_music()
