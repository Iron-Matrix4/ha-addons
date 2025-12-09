import tools
import config
import requests
import json

def play_media(entity_id, content_id, content_type="music"):
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: No config"

    url = f"{config.HA_URL}/api/services/media_player/play_media"
    headers = {
        "Authorization": f"Bearer {config.HA_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "entity_id": entity_id,
        "media_content_id": content_id,
        "media_content_type": content_type
    }
    
    try:
        print(f"Attempting to play '{content_id}' on {entity_id}...")
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print("Success!")
        print(response.text)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    # Test 1: Try a known Spotify URI (Rick Astley - Never Gonna Give You Up)
    # play_media("media_player.spotify_luke", "spotify:track:4cOdK2wGLETKBW3PvgPWqT")
    
    # Test 2: Try raw text (Unlikely to work on standard integration, but worth a shot)
    play_media("media_player.spotify_luke", "Never Gonna Give You Up")
