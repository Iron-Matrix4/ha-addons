import os
import subprocess
import webbrowser
import ctypes
import requests
import json
import config
import spotipy
import psutil
import pyperclip
import threading
import time
from ddgs import DDGS
from spotipy.oauth2 import SpotifyClientCredentials

# --- Home Assistant Integration ---

_LAST_INTERACTED_ENTITY = None

def get_last_interacted_entity():
    """
    Returns the entity_id of the last device successfully controlled.
    Useful for handling vague commands like "turn it off".
    """
    global _LAST_INTERACTED_ENTITY
    if _LAST_INTERACTED_ENTITY:
        return _LAST_INTERACTED_ENTITY
    return "None"

def control_home_assistant(entity_id: str, command: str = "turn_on", parameter: str = None):
    """
    Control a Home Assistant entity.
    
    Args:
        entity_id: The ID of the entity (e.g., "light.office", "climate.office").
        command: The action to perform ("turn_on", "turn_off", "toggle", "set_temperature", "turn_up", "turn_down").
        parameter: Optional. Parameter for the command (e.g., target temperature).
    """
    global _LAST_INTERACTED_ENTITY
    
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: Home Assistant URL or Token not configured."

    # Step 1: Resolve the entity ID (handles Light/Switch mismatch fallback)
    # This prevents sending 'light.turn_on' to a missing entity which might yield a false Success
    resolved_id, was_resolved = _resolve_entity(entity_id)
    entity_id = resolved_id # Update to the real ID
    domain = entity_id.split(".")[0]
    service = command

    # Temperature Helper Logic
    if command in ["turn_up", "turn_down"]:
        # We need the current state to know what to set it to
        # Note: get_ha_state calls _resolve_entity internally so it matches
        current_state_str = get_ha_state(entity_id)
        import re
        match = re.search(r"is ([\d\.]+)", current_state_str)
        if match:
            current_temp = float(match.group(1))
            new_temp = current_temp + 1.0 if command == "turn_up" else current_temp - 1.0
            service = "set_temperature"
            parameter = str(new_temp)
        else:
            return f"Could not determine current temperature to {command}. Result: {current_state_str}"

    # Map commands to services
    if command in ["on", "start"]:
        service = "turn_on"
    elif command in ["off", "stop"]:
        service = "turn_off"
    
    url = f"{config.HA_URL}/api/services/{domain}/{service}"
    
    headers = {
        "Authorization": f"Bearer {config.HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    data = {"entity_id": entity_id}
    
    if parameter:
        # If set_temperature, usually expects 'temperature' key
        if service == "set_temperature":
            data["temperature"] = float(parameter)
        # Fix: Do NOT send random parameters for turn_on/turn_off
        elif command in ["set_value", "set_cover_position"]:
             data["value"] = parameter
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # We still keep the detailed error check just in case resolution failed 
        # but simpler now since we tried our best upfront.
        if response.status_code in [400, 404, 500] or "entity not found" in response.text.lower():
             return f"Failed to control {entity_id}. Error {response.status_code}: {response.text}"

        response.raise_for_status()
        
        # Save Context for Follow-up commands
        _LAST_INTERACTED_ENTITY = entity_id
        
        msg = f"Success: Called {domain}.{service} on {entity_id}"
        if was_resolved:
            msg += f" (Auto-resolved)"
        if parameter:
            msg += f" with value {parameter}"
        return msg
    except Exception as e:
        return f"Failed to control {entity_id}: {e}"

def _search_ha_entities_raw(query: str):
    """
    Helper to search for Home Assistant entities.
    Returns a list of dicts: {'entity_id': str, 'friendly_name': str}
    """
    if not config.HA_URL or not config.HA_TOKEN:
        return []

    url = f"{config.HA_URL}/api/states"
    headers = {
        "Authorization": f"Bearer {config.HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        states = response.json()
        
        results = []
        query_tokens = query.lower().split()
        
        for entity in states:
            entity_id = entity['entity_id'].lower()
            friendly_name = entity['attributes'].get('friendly_name', '').lower()
            
            search_text = f"{entity_id} {friendly_name}"
            
            # Relevance Scoring
            score = 0
            
            # 1. Exact Friendly Name Match (Highest priority)
            if query == friendly_name:
                score = 100
            # 2. Query Phrase inside Friendly Name (e.g. "Office Light" in "Switch Office Light")
            elif query in friendly_name:
                score = 80
            # 3. All tokens in Friendly Name (scrambled but present)
            elif all(token in friendly_name for token in query_tokens):
                score = 60
            # 4. Phrase in Entity ID
            elif query in entity_id:
                score = 40
            # 5. Tokens in Entity ID
            elif all(token in entity_id for token in query_tokens):
                score = 20
            # 6. Fallback: Search text (Already passed filter, so low score)
            elif all(token in search_text for token in query_tokens):
                score = 10
            
            if score > 0:
                results.append({
                    'entity_id': entity['entity_id'],
                    'friendly_name': entity['attributes'].get('friendly_name', 'Unknown'),
                    'score': score
                })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    except Exception as e:
        print(f"Error searching entities: {e}")
        return []

def _resolve_entity(entity_id: str):
    """
    Attempt to resolve a potentially incorrect entity_id to a real one.
    Returns (resolved_entity_id, was_resolved)
    """
    if not config.HA_URL or not config.HA_TOKEN:
        return entity_id, False
        
    url = f"{config.HA_URL}/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {config.HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return entity_id, False # It acts exists
            
        if response.status_code == 404:
            # Entity not found, try to be smart and find it
            query_name = entity_id.split(".")[-1].replace("_", " ")
            found_entities = _search_ha_entities_raw(query_name)
            
            # Smart Selection with Plug Exclusion
            original_domain = entity_id.split(".")[0]
            target_domains = ['light', 'switch', 'input_boolean']
            
            for ent in found_entities:
                e_id = ent['entity_id']
                e_domain = e_id.split(".")[0]
                e_name = ent.get('friendly_name', '').lower()
                
                # Exclusion Rule: If looking for a light, don't fallback to a Plug/Socket
                if original_domain == "light" and ("plug" in e_name or "plug" in e_id or "socket" in e_name):
                    continue

                if e_domain in target_domains or e_domain == original_domain:
                     return e_id, True
            
    except Exception:
        pass
        
    return entity_id, False

def get_ha_state(entity_id: str):
    """Get the current state of a Home Assistant entity."""
    
    # Auto-resolve first
    resolved_id, was_resolved = _resolve_entity(entity_id)
    
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: Home Assistant URL or Token not configured."

    url = f"{config.HA_URL}/api/states/{resolved_id}"
    headers = {
        "Authorization": f"Bearer {config.HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        state_data = response.json()
        
        # Add unit_of_measurement if available for better context
        state_val = state_data['state']
        unit = state_data['attributes'].get('unit_of_measurement', '')
        if unit:
            state_val = f"{state_val} {unit}"
            
        msg = f"The state of {resolved_id} is {state_val}."
        if was_resolved:
            msg += f" (Automatically resolved from '{entity_id}' to '{resolved_id}')"
        return msg
    except Exception as e:
        return f"Failed to get state for {entity_id}: {e}"

def search_ha_entities(query: str):
    """
    Search for Home Assistant entities by name.
    Useful when you don't know the exact entity_id.
    """
    try:
        results = _search_ha_entities_raw(query)
        
        if not results:
            return f"No entities found matching '{query}'."
        
        # Format for LLM
        output = ["Found entities:"]
        for res in results[:10]:
            output.append(f"{res['entity_id']} ({res['friendly_name']})")
            
        return "\n".join(output)
    except Exception as e:
        return f"Failed to search entities: {e}"

# --- Spotify Control ---
def play_music(query: str, entity_id: str = "media_player.spotify_luke"):
    """
    Play music on Spotify.
    Searches for the song/artist/album on Spotify and plays it on the specified Home Assistant media player.
    """
    if not config.SPOTIPY_CLIENT_ID or not config.SPOTIPY_CLIENT_SECRET:
        return "Error: Spotify credentials not configured."
        
    try:
        # Pre-check: Ensure Spotify is active
        # We check the attributes of the media player in HA.
        # If 'source_list' is missing, it usually means the device isn't fully active/connected.
        url_state = f"{config.HA_URL}/api/states/{entity_id}"
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json",
        }
        
        needs_launch = False
        try:
            state_res = requests.get(url_state, headers=headers).json()
            if 'source_list' not in state_res.get('attributes', {}):
                needs_launch = True
                print(f"Spotify entity {entity_id} missing source_list. Launching...")
        except Exception:
            needs_launch = True # Assume not ready if check fails

        if needs_launch:
            # Launch and Kickstart
            open_application("spotify")
            time.sleep(8) 
            print("Sending Media Play Key to wake up session...")
            media_play_pause()
            time.sleep(3)

        # 1. Search Spotify
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=config.SPOTIPY_CLIENT_ID,
            client_secret=config.SPOTIPY_CLIENT_SECRET
        ))
        
        # Try to find a track first, then album, then artist, then playlist
        results = sp.search(q=query, limit=1, type='track,album,artist,playlist')
        
        uri = None
        found_name = None
        found_type = None
        
        if results['tracks']['items']:
            item = results['tracks']['items'][0]
            uri = item['uri']
            found_name = f"{item['name']} by {item['artists'][0]['name']}"
            found_type = "music"
        elif results['albums']['items']:
            item = results['albums']['items'][0]
            uri = item['uri']
            found_name = item['name']
            found_type = "album"
        elif results['artists']['items']:
            item = results['artists']['items'][0]
            uri = item['uri']
            found_name = item['name']
            found_type = "music"
        elif results['playlists']['items']:
            item = results['playlists']['items'][0]
            uri = item['uri']
            found_name = item['name']
            found_type = "playlist"
            
        if not uri:
            return f"Could not find '{query}' on Spotify."
            
        # 2. Tell Home Assistant to play it
        print(f"Playing {uri} on {entity_id}")
        url_play = f"{config.HA_URL}/api/services/media_player/play_media"
        data = {
            "entity_id": entity_id,
            "media_content_id": uri,
            "media_content_type": found_type
        }
        
        # Attempt 1
        response = requests.post(url_play, headers=headers, json=data)
        
        # Double check: if it still failed despite our efforts (500 error or similar)
        if response.status_code == 500 and not needs_launch:
             # Retry launch logic one more time if we hadn't already
             print("Spotify 500 error on playback. Launching fallback...")
             open_application("spotify")
             time.sleep(8)
             media_play_pause()
             time.sleep(3)
             response = requests.post(url_play, headers=headers, json=data)

        if response.status_code == 500:
               return f"Failed to play on {entity_id} (Server Error). Tried launching Spotify but it failed. Please ensure the device is active."

        response.raise_for_status()
        
        return f"Playing '{found_name}' on {entity_id}."
        
    except Exception as e:
        return f"Failed to play music: {e}"

# --- Advanced Tools ---

def get_weather(city: str = "London"):
    """
    Get the current weather for a specific city.
    Uses OpenMeteo API.
    """
    try:
        # 1. Geocoding to get lat/long
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url).json()
        
        if not geo_res.get('results'):
            return f"Could not find city: {city}"
            
        lat = geo_res['results'][0]['latitude']
        lon = geo_res['results'][0]['longitude']
        name = geo_res['results'][0]['name']
        
        # 2. Get Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url).json()
        
        current = weather_res['current_weather']
        temp = current['temperature']
        wind = current['windspeed']
        
        return f"Weather in {name}: {temp}°C, Wind: {wind} km/h."
    except Exception as e:
        return f"Failed to get weather: {e}"

def get_system_status():
    """
    Get current system status (CPU and RAM usage).
    """
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        return f"CPU Usage: {cpu}%\nRAM Usage: {memory.percent}% ({round(memory.used/1024/1024/1024, 1)}GB used of {round(memory.total/1024/1024/1024, 1)}GB)"
    except Exception as e:
        return f"Failed to get system status: {e}"

def google_search(query: str):
    """
    Perform a web search (using DuckDuckGo) and return the top results.
    """
    try:
        results = []
        with DDGS() as ddgs:
            # max_results was renamed/changed in newer versions, usually it's just 'max_results' or 'limit'
            # The library changes often. standardizing on .text() with max_results
            ddg_results = list(ddgs.text(query, max_results=6))
            
        for result in ddg_results:
            title = result.get('title', 'No Title')
            body = result.get('body', result.get('href', ''))
            results.append(f"- {title}: {body}")
        
        if not results:
            return "No results found."
            
        return "Top Search Results:\n" + "\n".join(results)
    except Exception as e:
        return f"Search failed: {e}"

def set_timer(seconds: int):
    """
    Set a timer for a specific number of seconds.
    The timer runs in the background and will alert when finished.
    """
    def timer_thread():
        time.sleep(seconds)
        # We need a way to speak asynchronously. 
        # For now, we'll just print, but ideally this would trigger the TTS engine.
        # Since TTS is in main loop, we might need a callback or just print for now.
        print(f"\n[TIMER] Timer for {seconds} seconds finished!\n")
        # TODO: Integrate with TTS for audible alarm
        
    t = threading.Thread(target=timer_thread)
    t.daemon = True
    t.start()
    
    return f"Timer set for {seconds} seconds."

def read_clipboard():
    """Read the current text from the clipboard."""
    return pyperclip.paste()

def write_to_clipboard(text: str):
    """Write text to the clipboard."""
    pyperclip.copy(text)
    return "Copied to clipboard."

# --- System Control ---
def shutdown_pc():
    """Shut down the computer immediately."""
    os.system("shutdown /s /t 1")
    return "Shutting down PC..."

def restart_pc():
    """Restart the computer immediately."""
    os.system("shutdown /r /t 1")
    return "Restarting PC..."

def lock_pc():
    """Lock the Windows workstation."""
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "PC Locked."

def sleep_pc():
    """Put the computer to sleep."""
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "PC going to sleep..."

# --- Volume Control ---
def set_volume_mute(mute: bool = True):
    """Mute or unmute the system volume."""
    APPCOMMAND_VOLUME_MUTE = 0x80000
    WM_APPCOMMAND = 0x319
    ctypes.windll.user32.SendMessageW(0xffff, WM_APPCOMMAND, 0, APPCOMMAND_VOLUME_MUTE)
    return "Volume mute toggled."

def volume_up():
    """Increase system volume."""
    APPCOMMAND_VOLUME_UP = 0xA0000
    WM_APPCOMMAND = 0x319
    ctypes.windll.user32.SendMessageW(0xffff, WM_APPCOMMAND, 0, APPCOMMAND_VOLUME_UP)
    return "Volume increased."

def volume_down():
    """Decrease system volume."""
    APPCOMMAND_VOLUME_DOWN = 0x90000
    WM_APPCOMMAND = 0x319
    ctypes.windll.user32.SendMessageW(0xffff, WM_APPCOMMAND, 0, APPCOMMAND_VOLUME_DOWN)
    return "Volume decreased."

# --- App Control ---
def open_application(app_name: str):
    """
    Open a specific application by name.
    Supported: calculator, notepad, chrome, spotify, code (vscode), explorer, cmd.
    """
    apps = {
        "calculator": "calc.exe",
        "notepad": "notepad.exe",
        "chrome": "chrome",
        "spotify": os.path.expanduser('~\\AppData\\Local\\Microsoft\\WindowsApps\\Spotify.exe'), # Fixed path for Windows Store version
        "code": "code",
        "vscode": "code",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "terminal": "wt.exe"
    }
    
    target = apps.get(app_name.lower())
    if target:
        try:
            subprocess.Popen(target, shell=True)
            return f"Opened {app_name}"
        except Exception as e:
            return f"Failed to open {app_name}: {e}"
    else:
        try:
            os.startfile(app_name)
            return f"Attempted to launch {app_name}"
        except Exception:
            return f"Application '{app_name}' not found."

def open_url(url: str):
    """Open a website in the default browser."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"

# --- Media Control ---
def media_play_pause():
    """Toggle Play/Pause on active media."""
    APPCOMMAND_MEDIA_PLAY_PAUSE = 0xE0000
    WM_APPCOMMAND = 0x319
    ctypes.windll.user32.SendMessageW(0xffff, WM_APPCOMMAND, 0, APPCOMMAND_MEDIA_PLAY_PAUSE)
    return "Media Play/Pause toggled."

def media_next():
    """Skip to next track."""
    APPCOMMAND_MEDIA_NEXTTRACK = 0xB0000
    WM_APPCOMMAND = 0x319
    ctypes.windll.user32.SendMessageW(0xffff, WM_APPCOMMAND, 0, APPCOMMAND_MEDIA_NEXTTRACK)
    return "Skipped to next track."

def media_prev():
    """Skip to previous track."""
    APPCOMMAND_MEDIA_PREVIOUSTRACK = 0xC0000
    WM_APPCOMMAND = 0x319
    ctypes.windll.user32.SendMessageW(0xffff, WM_APPCOMMAND, 0, APPCOMMAND_MEDIA_PREVIOUSTRACK)
    return "Skipped to previous track."

# --- Tool Registry ---
def get_tools():
    return [
        get_ha_state,
        search_ha_entities,
        control_home_assistant,
        get_last_interacted_entity,
        play_music,
        get_weather,
        get_system_status,
        google_search,
        set_timer,
        read_clipboard,
        write_to_clipboard,
        shutdown_pc,
        restart_pc,
        lock_pc,
        sleep_pc,
        set_volume_mute,
        volume_up,
        volume_down,
        open_application,
        open_url,
        media_play_pause,
        media_next,
        media_prev
    ]
