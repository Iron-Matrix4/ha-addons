"""
Tool functions for Jarvis Home Assistant Add-on.
Provides Home Assistant control, Spotify, Radarr, Sonarr, web search, and contextual knowledge.
"""
import requests
import json
import time
import threading
import logging
from typing import Optional
import config_helper as config

# Spotify support (optional)
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False

# No additional imports needed for Google Custom Search (uses requests)

logger = logging.getLogger(__name__)

# Global context for follow-up commands
_LAST_INTERACTED_ENTITY = None

# ===== HOME ASSISTANT CONTROL =====

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
        command: The action to perform ("turn_on", "turn_off", "toggle", "set_temperature", "set_hvac_mode", "turn_up", "turn_down").
        parameter: Optional. Parameter for the command (e.g., target temperature or hvac_mode like "heat", "cool", "auto", "off").
    """
    global _LAST_INTERACTED_ENTITY
    
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: Home Assistant URL or Token not configured."

    # Resolve the entity ID (handles Light/Switch mismatch fallback)
    resolved_id, was_resolved = _resolve_entity(entity_id)
    entity_id = resolved_id
    domain = entity_id.split(".")[0]
    service = command

    # Temperature Helper Logic
    if command in ["turn_up", "turn_down"]:
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
    elif command == "close":
        service = "close_cover" if domain == "cover" else "turn_off"
    elif command == "open":
        service = "open_cover" if domain == "cover" else "turn_on"
    elif command == "stop":
        service = "stop_cover" if domain == "cover" else "turn_off"
    elif command == "lock":
        service = "lock"
    elif command == "unlock":
        service = "unlock"
    elif command == "set_brightness":
        service = "turn_on"  # Use turn_on with brightness parameter
    elif command == "set_color":
        service = "turn_on"  # Use turn_on with color parameter
    elif command in ["play", "pause", "media_play", "media_pause"]:
        service = f"media_{command.replace('media_', '')}"
    elif command in ["volume_up", "volume_down", "media_next", "media_previous"]:
        service = command
    
    url = f"{config.HA_URL}/api/services/{domain}/{service}"
    
    headers = {
        "Authorization": f"Bearer {config.HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    data = {"entity_id": entity_id}
    
    if parameter:
        if service == "set_temperature":
            data["temperature"] = float(parameter)
        elif service == "set_hvac_mode":
            data["hvac_mode"] = parameter  # heat, cool, auto, off, etc.
        elif service == "set_cover_position":
            data["position"] = int(parameter)  # 0-100
        elif command == "set_brightness":
            # Brightness can be 0-255 or 0-100 depending on how user specifies
            brightness = int(parameter)
            if brightness <= 100:
                brightness = int(brightness * 2.55)  # Convert percentage to 0-255
            data["brightness"] = brightness
        elif command == "set_color":
            # Parameter should be color name like "red", "blue" or RGB like "255,0,0"
            if "," in parameter:
                # RGB format
                rgb = [int(x.strip()) for x in parameter.split(",")]
                data["rgb_color"] = rgb
            else:
                # Color name
                data["color_name"] = parameter
        elif command in ["set_value", "set_cover_position"]:
             data["value"] = parameter
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
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
            
            if query == friendly_name:
                score = 100
            elif query in friendly_name:
                score = 80
            elif all(token in friendly_name for token in query_tokens):
                score = 60
            elif query in entity_id:
                score = 40
            elif all(token in entity_id for token in query_tokens):
                score = 20
            elif all(token in search_text for token in query_tokens):
                score = 10
            
            if score > 0:
                results.append({
                    'entity_id': entity['entity_id'],
                    'friendly_name': entity['attributes'].get('friendly_name', 'Unknown'),
                    'score': score
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    except Exception as e:
        logger.error(f"Error searching entities: {e}")
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
            return entity_id, False
            
        if response.status_code == 404:
            query_name = entity_id.split(".")[-1].replace("_", " ")
            found_entities = _search_ha_entities_raw(query_name)
            
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
        
        output = ["Found entities:"]
        for res in results[:10]:
            output.append(f"{res['entity_id']} ({res['friendly_name']})")
            
        return "\n".join(output)
    except Exception as e:
        return f"Failed to search entities: {e}"

# ===== SPOTIFY CONTROL =====

def play_music(query: str, device: str = None, entity_id: str = None):
    """
    Play music on Spotify using Spotcast.
    Searches Spotify and plays on the specified device using Spotcast integration.
    
    Args:
        query: Song, artist, or album to search for
        device: Device name or entity_id to play on (e.g., "Office Display", "media_player.office_display")
        entity_id: Optional specific entity_id (overrides device name search)
    """
    if not SPOTIFY_AVAILABLE:
        return "Error: Spotify library (spotipy) not installed."
    
    if not config.SPOTIPY_CLIENT_ID or not config.SPOTIPY_CLIENT_SECRET:
        return "Error: Spotify credentials not configured."
        
    try:
        # Search Spotify
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=config.SPOTIPY_CLIENT_ID,
            client_secret=config.SPOTIPY_CLIENT_SECRET
        ))
        
        results = sp.search(q=query, limit=1, type='track,album,artist,playlist')
        
        uri = None
        found_name = None
        
        if results['tracks']['items']:
            item = results['tracks']['items'][0]
            uri = item['uri']
            found_name = f"{item['name']} by {item['artists'][0]['name']}"
        elif results['albums']['items']:
            item = results['albums']['items'][0]
            uri = item['uri']
            found_name = f"Album: {item['name']}"
        elif results['artists']['items']:
            item = results['artists']['items'][0]
            uri = item['uri']
            found_name = f"Artist: {item['name']}"
        elif results['playlists']['items']:
            item = results['playlists']['items'][0]
            uri = item['uri']
            found_name = f"Playlist: {item['name']}"
            
        if not uri:
            return f"Could not find '{query}' on Spotify."
        
        # If no device specified, need to ask
        if not device and not entity_id:
            # Get available media players
            headers = {
                "Authorization": f"Bearer {config.HA_TOKEN}",
                "Content-Type": "application/json",
            }
            entities_url = f"{config.HA_URL}/api/states"
            response = requests.get(entities_url, headers=headers)
            response.raise_for_status()
            
            media_players = []
            for entity in response.json():
                if entity['entity_id'].startswith('media_player.'):
                    name = entity['attributes'].get('friendly_name', entity['entity_id'])
                    media_players.append(name)
            
            if media_players:
                devices_list = ', '.join(media_players[:10])  # Limit to 10
                return f"Found '{found_name}'. Which device? Available: {devices_list}"
            else:
                return "No media players found. Please specify a device."
        
        # Find the target device entity_id
        target_entity = entity_id
        if device and not entity_id:
            # Search for matching media player
            headers = {
                "Authorization": f"Bearer {config.HA_TOKEN}",
                "Content-Type": "application/json",
            }
            entities_url = f"{config.HA_URL}/api/states"
            response = requests.get(entities_url, headers=headers)
            response.raise_for_status()
            
            device_lower = device.lower()
            for entity in response.json():
                if entity['entity_id'].startswith('media_player.'):
                    entity_id_match = device_lower in entity['entity_id'].lower()
                    name_match = device_lower in entity['attributes'].get('friendly_name', '').lower()
                    
                    if entity_id_match or name_match:
                        target_entity = entity['entity_id']
                        break
            
            if not target_entity:
                return f"Could not find device matching '{device}'"
        
        # Use Spotcast to play
        logger.info(f"Playing {uri} on {target_entity} via Spotcast")
        
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json",
        }
        spotcast_url = f"{config.HA_URL}/api/services/spotcast/start"
        spotcast_data = {
            "entity_id": target_entity,
            "uri": uri,
        }
        
        response = requests.post(spotcast_url, headers=headers, json=spotcast_data)
        response.raise_for_status()
        
        return f"Playing '{found_name}' on {target_entity.replace('media_player.', '').replace('_', ' ').title()}."
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            return f"Spotcast error: {e.response.text}. Make sure Spotcast is configured and the device supports Spotify."
        logger.error(f"Error in play_music: {e}", exc_info=True)
        return f"Failed to play music: {e}"
    except Exception as e:
        logger.error(f"Error in play_music: {e}", exc_info=True)
        return f"Failed to play music: {e}"


# ===== RADARR INTEGRATION =====

def query_radarr(query_type: str, movie_name: str = None):
    """
    Query Radarr for information about movies and system status.
    
    Args:
        query_type: Type of query:
            - "status" - Is Radarr running?
            - "stats" - Library statistics (total, 4K, missing counts)
            - "last_downloaded" - Most recently downloaded film
            - "recent" - Recent downloads/activity
            - "search" - Search for a movie by name
            - "missing" - List missing/wanted movies
        movie_name: Movie name (required for "search")
    """
    if not config.RADARR_URL or not config.RADARR_API_KEY:
        return "Error: Radarr URL or API key not configured."
    
    headers = {
        "X-Api-Key": config.RADARR_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        if query_type == "status":
            # Check system status
            url = f"{config.RADARR_URL}/api/v3/system/status"
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            status = response.json()
            
            version = status.get('version', 'Unknown')
            return f"Radarr is running. Version: {version}"
        
        elif query_type == "stats":
            # Get library statistics
            url = f"{config.RADARR_URL}/api/v3/movie"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            movies = response.json()
            
            total = len(movies)
            has_file = sum(1 for m in movies if m.get('hasFile', False))
            missing = sum(1 for m in movies if m.get('monitored', False) and not m.get('hasFile', False))
            
            # Count 4K movies (look for quality profile or file quality)
            count_4k = 0
            for movie in movies:
                if movie.get('hasFile'):
                    movie_file = movie.get('movieFile', {})
                    quality = movie_file.get('quality', {}).get('quality', {}).get('name', '')
                    if '2160' in quality or '4k' in quality.lower() or 'uhd' in quality.lower():
                        count_4k += 1
            
            return f"Radarr Library Stats: {total} movies total, {has_file} downloaded, {missing} missing, approximately {count_4k} in 4K"
        
        elif query_type == "last_downloaded":
            # Get movie history for recent downloads
            url = f"{config.RADARR_URL}/api/v3/history"
            params = {"pageSize": 20, "sortKey": "date", "sortDirection": "descending"}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            history = response.json()
            
            records = history.get('records', [])
            for record in records:
                if record.get('eventType') == 'downloadFolderImported':
                    movie = record.get('movie', {})
                    title = movie.get('title', 'Unknown')
                    year = movie.get('year', '')
                    date = record.get('date', '')[:10]  # Just the date part
                    quality = record.get('quality', {}).get('quality', {}).get('name', 'Unknown')
                    return f"Last downloaded: {title} ({year}) on {date} in {quality}"
            
            return "No recent downloads found in Radarr history."
        
        elif query_type == "recent":
            # Get recent activity
            url = f"{config.RADARR_URL}/api/v3/history"
            params = {"pageSize": 10, "sortKey": "date", "sortDirection": "descending"}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            history = response.json()
            
            records = history.get('records', [])
            if not records:
                return "No recent activity in Radarr."
            
            output = ["Recent Radarr Activity:"]
            for record in records[:5]:
                movie = record.get('movie', {})
                title = movie.get('title', 'Unknown')
                event = record.get('eventType', 'Unknown')
                date = record.get('date', '')[:10]
                
                event_desc = {
                    'grabbed': 'Started downloading',
                    'downloadFolderImported': 'Downloaded',
                    'downloadFailed': 'Failed'
                }.get(event, event)
                
                output.append(f"- {event_desc}: {title} ({date})")
            
            return "\n".join(output)
        
        elif query_type == "search" and movie_name:
            # Search for movie on TMDB via Radarr
            url = f"{config.RADARR_URL}/api/v3/movie/lookup"
            params = {"term": movie_name}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            
            if not results:
                return f"No movies found matching '{movie_name}'."
            
            output = [f"Found {len(results)} results:"]
            for movie in results[:5]:
                title = movie.get('title', 'Unknown')
                year = movie.get('year', 'Unknown')
                output.append(f"- {title} ({year})")
            
            return "\n".join(output)
        
        elif query_type == "missing":
            url = f"{config.RADARR_URL}/api/v3/wanted/missing"
            response = requests.get(url, headers=headers, params={"pageSize": 10})
            response.raise_for_status()
            result = response.json()
            
            records = result.get('records', [])
            total_missing = result.get('totalRecords', len(records))
            
            if not records:
                return "No missing movies in Radarr."
            
            output = [f"Missing movies ({total_missing} total):"]
            for movie in records[:10]:
                title = movie.get('title', 'Unknown')
                year = movie.get('year', 'Unknown')
                output.append(f"- {title} ({year})")
            
            return "\n".join(output)
        
        else:
            return f"Unknown query type: {query_type}. Supported: status, stats, last_downloaded, recent, search, missing"
    
    except requests.exceptions.ConnectionError:
        return "Radarr is not responding. It may be offline or the URL is incorrect."
    except requests.exceptions.Timeout:
        return "Radarr connection timed out. It may be slow or unresponsive."
    except Exception as e:
        return f"Radarr error: {e}"


def add_to_radarr(movie_name: str):
    """
    Add a movie to Radarr by name.
    
    Args:
        movie_name: Name of the movie to add
    """
    if not config.RADARR_URL or not config.RADARR_API_KEY:
        return "Error: Radarr URL or API key not configured."
    
    headers = {
        "X-Api-Key": config.RADARR_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Search first
        url = f"{config.RADARR_URL}/api/v3/movie/lookup"
        params = {"term": movie_name}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()
        
        if not results:
            return f"No movies found matching '{movie_name}'."
        
        # Add first result
        movie = results[0]
        
        # Get root folder
        root_url = f"{config.RADARR_URL}/api/v3/rootfolder"
        root_response = requests.get(root_url, headers=headers)
        root_response.raise_for_status()
        root_folders = root_response.json()
        
        if not root_folders:
            return "Error: No root folder configured in Radarr."
        
        # Get quality profile
        profile_url = f"{config.RADARR_URL}/api/v3/qualityprofile"
        profile_response = requests.get(profile_url, headers=headers)
        profile_response.raise_for_status()
        profiles = profile_response.json()
        
        if not profiles:
            return "Error: No quality profile configured in Radarr."
        
        # Add movie
        add_data = {
            "title": movie['title'],
            "tmdbId": movie['tmdbId'],
            "year": movie['year'],
            "qualityProfileId": profiles[0]['id'],
            "rootFolderPath": root_folders[0]['path'],
            "monitored": True,
            "addOptions": {
                "searchForMovie": True
            }
        }
        
        add_url = f"{config.RADARR_URL}/api/v3/movie"
        add_response = requests.post(add_url, headers=headers, json=add_data)
        add_response.raise_for_status()
        
        return f"Added '{movie['title']} ({movie['year']})' to Radarr and started searching."
    
    except Exception as e:
        return f"Radarr error: {e}"


# Keep legacy function for backwards compatibility
def control_radarr(action: str, movie_name: str = None):
    """Legacy function - use query_radarr or add_to_radarr instead."""
    if action in ["status", "stats", "last_downloaded", "recent", "missing"]:
        return query_radarr(action, movie_name)
    elif action == "search":
        return query_radarr("search", movie_name)
    elif action == "add":
        return add_to_radarr(movie_name)
    else:
        return query_radarr(action, movie_name)

# ===== SONARR INTEGRATION =====

def query_sonarr(query_type: str, series_name: str = None):
    """
    Query Sonarr for information about TV series and system status.
    
    Args:
        query_type: Type of query:
            - "status" - Is Sonarr running?
            - "stats" - Library statistics (total series, episodes, missing)
            - "last_downloaded" - Most recently downloaded episode
            - "recent" - Recent downloads/activity
            - "search" - Search for a series by name
            - "missing" - List missing/wanted episodes
        series_name: Series name (required for "search")
    """
    if not config.SONARR_URL or not config.SONARR_API_KEY:
        return "Error: Sonarr URL or API key not configured."
    
    headers = {
        "X-Api-Key": config.SONARR_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        if query_type == "status":
            # Check system status
            url = f"{config.SONARR_URL}/api/v3/system/status"
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            status = response.json()
            
            version = status.get('version', 'Unknown')
            return f"Sonarr is running. Version: {version}"
        
        elif query_type == "stats":
            # Get library statistics
            url = f"{config.SONARR_URL}/api/v3/series"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            series_list = response.json()
            
            total_series = len(series_list)
            total_episodes = sum(s.get('episodeFileCount', 0) for s in series_list)
            total_seasons = sum(s.get('seasonCount', 0) for s in series_list)
            missing = sum(s.get('episodeCount', 0) - s.get('episodeFileCount', 0) for s in series_list if s.get('monitored', False))
            
            return f"Sonarr Library Stats: {total_series} TV shows, {total_seasons} seasons, {total_episodes} episodes downloaded, approximately {missing} episodes missing"
        
        elif query_type == "last_downloaded":
            # Get episode history for recent downloads
            url = f"{config.SONARR_URL}/api/v3/history"
            params = {"pageSize": 20, "sortKey": "date", "sortDirection": "descending"}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            history = response.json()
            
            records = history.get('records', [])
            for record in records:
                if record.get('eventType') == 'downloadFolderImported':
                    series = record.get('series', {})
                    episode = record.get('episode', {})
                    series_title = series.get('title', 'Unknown')
                    season = episode.get('seasonNumber', '?')
                    ep_num = episode.get('episodeNumber', '?')
                    ep_title = episode.get('title', 'Unknown')
                    date = record.get('date', '')[:10]
                    quality = record.get('quality', {}).get('quality', {}).get('name', 'Unknown')
                    
                    return f"Last downloaded: {series_title} S{season:02d}E{ep_num:02d} '{ep_title}' on {date} in {quality}"
            
            return "No recent downloads found in Sonarr history."
        
        elif query_type == "recent":
            # Get recent activity
            url = f"{config.SONARR_URL}/api/v3/history"
            params = {"pageSize": 10, "sortKey": "date", "sortDirection": "descending"}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            history = response.json()
            
            records = history.get('records', [])
            if not records:
                return "No recent activity in Sonarr."
            
            output = ["Recent Sonarr Activity:"]
            for record in records[:5]:
                series = record.get('series', {})
                episode = record.get('episode', {})
                series_title = series.get('title', 'Unknown')
                season = episode.get('seasonNumber', '?')
                ep_num = episode.get('episodeNumber', '?')
                event = record.get('eventType', 'Unknown')
                date = record.get('date', '')[:10]
                
                event_desc = {
                    'grabbed': 'Started downloading',
                    'downloadFolderImported': 'Downloaded',
                    'downloadFailed': 'Failed'
                }.get(event, event)
                
                output.append(f"- {event_desc}: {series_title} S{season:02d}E{ep_num:02d} ({date})")
            
            return "\n".join(output)
        
        elif query_type == "search" and series_name:
            url = f"{config.SONARR_URL}/api/v3/series/lookup"
            params = {"term": series_name}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            
            if not results:
                return f"No series found matching '{series_name}'."
            
            output = [f"Found {len(results)} results:"]
            for series in results[:5]:
                title = series.get('title', 'Unknown')
                year = series.get('year', 'Unknown')
                output.append(f"- {title} ({year})")
            
            return "\n".join(output)
        
        elif query_type == "missing":
            url = f"{config.SONARR_URL}/api/v3/wanted/missing"
            response = requests.get(url, headers=headers, params={"pageSize": 20})
            response.raise_for_status()
            result = response.json()
            
            records = result.get('records', [])
            total_missing = result.get('totalRecords', len(records))
            
            if not records:
                return "No missing episodes in Sonarr."
            
            output = [f"Missing episodes ({total_missing} total):"]
            for ep in records[:10]:
                series_title = ep.get('series', {}).get('title', 'Unknown')
                season = ep.get('seasonNumber', '?')
                episode = ep.get('episodeNumber', '?')
                title = ep.get('title', 'Unknown')
                output.append(f"- {series_title} S{season:02d}E{episode:02d}: {title}")
            
            return "\n".join(output)
        
        else:
            return f"Unknown query type: {query_type}. Supported: status, stats, last_downloaded, recent, search, missing"
    
    except requests.exceptions.ConnectionError:
        return "Sonarr is not responding. It may be offline or the URL is incorrect."
    except requests.exceptions.Timeout:
        return "Sonarr connection timed out. It may be slow or unresponsive."
    except Exception as e:
        return f"Sonarr error: {e}"


def add_to_sonarr(series_name: str):
    """
    Add a TV series to Sonarr by name.
    
    Args:
        series_name: Name of the series to add
    """
    if not config.SONARR_URL or not config.SONARR_API_KEY:
        return "Error: Sonarr URL or API key not configured."
    
    headers = {
        "X-Api-Key": config.SONARR_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Search first
        url = f"{config.SONARR_URL}/api/v3/series/lookup"
        params = {"term": series_name}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()
        
        if not results:
            return f"No series found matching '{series_name}'."
        
        series = results[0]
        
        # Get root folder
        root_url = f"{config.SONARR_URL}/api/v3/rootfolder"
        root_response = requests.get(root_url, headers=headers)
        root_response.raise_for_status()
        root_folders = root_response.json()
        
        if not root_folders:
            return "Error: No root folder configured in Sonarr."
        
        # Get quality profile
        profile_url = f"{config.SONARR_URL}/api/v3/qualityprofile"
        profile_response = requests.get(profile_url, headers=headers)
        profile_response.raise_for_status()
        profiles = profile_response.json()
        
        if not profiles:
            return "Error: No quality profile configured in Sonarr."
        
        # Add series
        add_data = {
            "title": series['title'],
            "tvdbId": series.get('tvdbId'),
            "qualityProfileId": profiles[0]['id'],
            "rootFolderPath": root_folders[0]['path'],
            "monitored": True,
            "addOptions": {
                "searchForMissingEpisodes": True
            }
        }
        
        add_url = f"{config.SONARR_URL}/api/v3/series"
        add_response = requests.post(add_url, headers=headers, json=add_data)
        add_response.raise_for_status()
        
        return f"Added '{series['title']}' to Sonarr and started searching for episodes."
    
    except Exception as e:
        return f"Sonarr error: {e}"


# Keep legacy function for backwards compatibility
def control_sonarr(action: str, series_name: str = None):
    """Legacy function - use query_sonarr or add_to_sonarr instead."""
    if action in ["status", "stats", "last_downloaded", "recent", "missing"]:
        return query_sonarr(action, series_name)
    elif action == "search":
        return query_sonarr("search", series_name)
    elif action == "add":
        return add_to_sonarr(series_name)
    elif action == "list_missing":
        return query_sonarr("missing", series_name)
    else:
        return query_sonarr(action, series_name)

# ===== WEB SEARCH & KNOWLEDGE =====

def google_search(query: str):
    """
    Perform a web search using Google Custom Search API.
    Use this to answer general knowledge questions.
    """
    if not config.GOOGLE_SEARCH_API_KEY or not config.GOOGLE_SEARCH_ENGINE_ID:
        return "Error: Google Custom Search not configured. Please add API key and Search Engine ID to add-on configuration."
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": config.GOOGLE_SEARCH_API_KEY,
            "cx": config.GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": 5  # Number of results (max 10)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        items = data.get('items', [])
        if not items:
            return f"No results found for '{query}'."
        
        results = ["Top Search Results:"]
        for item in items:
            title = item.get('title', 'No Title')
            snippet = item.get('snippet', 'No description')
            results.append(f"- {title}: {snippet}")
        
        return "\n".join(results)
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return "Search quota exceeded. Google Custom Search free tier is limited to 100 queries/day."
        else:
            return f"Google Search API error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Search failed: {e}"

def get_contextual_answer(entity_id: str, question: str):
    """
    Get a contextual answer by combining HA state with web search.
    
    Example: "What's my fish tank temperature?"
    1. Get current temp from HA
    2. Search for "ideal fish tank temperature"
    3. Return: "Your tank is 24°C, which is ideal for tropical fish (24-26°C)"
    
    Args:
        entity_id: The HA entity to query (e.g., "sensor.fish_tank_temp")
        question: Contextual question to search (e.g., "ideal fish tank temperature")
    """
    try:
        # Get current state from HA (ALWAYS live, never cached!)
        current_state = get_ha_state(entity_id)
        
        # Search web for context
        search_result = google_search(question)
        
        # Return both for AI to synthesize
        return f"Current State: {current_state}\n\nContext from Web:\n{search_result}\n\nPlease synthesize this information for the user."
    
    except Exception as e:
        return f"Failed to get contextual answer: {e}"

# ===== UTILITY TOOLS =====

def get_weather(city: str = "London", forecast_hours: int = 12):
    """
    Get comprehensive weather including current conditions and hourly forecast with precipitation.
    Uses OpenMeteo API (free, no API key needed).
    
    Args:
        city: City name to get weather for
        forecast_hours: Number of hours to forecast (default 12)
    """
    try:
        # Geocoding to get lat/long
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url).json()
        
        if not geo_res.get('results'):
            return f"Could not find city: {city}"
            
        lat = geo_res['results'][0]['latitude']
        lon = geo_res['results'][0]['longitude']
        name = geo_res['results'][0]['name']
        
        # Get comprehensive weather including hourly forecast
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&hourly=temperature_2m,precipitation_probability,precipitation,rain,weathercode"
            f"&forecast_days=1"
            f"&timezone=auto"
        )
        weather_res = requests.get(weather_url).json()
        
        current = weather_res['current_weather']
        temp = current['temperature']
        wind = current['windspeed']
        
        # Build response with current conditions
        response = [f"Weather in {name}:"]
        response.append(f"Current: {temp}°C, Wind: {wind} km/h")
        
        # Analyze hourly forecast for next few hours
        hourly = weather_res.get('hourly', {})
        if hourly:
            times = hourly.get('time', [])
            precip_prob = hourly.get('precipitation_probability', [])
            precip_amount = hourly.get('precipitation', [])
            rain_amount = hourly.get('rain', [])
            
            # Check if rain is expected in the forecast period
            max_rain_prob = max(precip_prob[:forecast_hours]) if precip_prob else 0
            total_precip = sum(precip_amount[:forecast_hours]) if precip_amount else 0
            
            if max_rain_prob > 30 or total_precip > 0:
                response.append(f"\n⚠️ Rain likely in next {forecast_hours} hours:")
                response.append(f"Max precipitation probability: {max_rain_prob}%")
                if total_precip > 0:
                    response.append(f"Expected rainfall: {total_precip:.1f}mm")
                response.append("🌂 Recommendation: Bring an umbrella!")
            else:
                response.append(f"\n✅ No significant rain expected in next {forecast_hours} hours")
                response.append("No umbrella needed!")
        
        return "\n".join(response)
        
    except Exception as e:
        logger.error(f"Weather error: {e}", exc_info=True)
        return f"Failed to get weather: {e}"

def get_travel_time(origin: str, destination: str, mode: str = "driving"):
    """
    Get travel time between two locations with current traffic conditions.
    Uses Google Maps Distance Matrix API.
    
    Args:
        origin: Starting location (address or place name)
        destination: Destination (address or place name)
        mode: Travel mode - "driving", "walking", "bicycling", "transit"
    """
    if not config.GOOGLE_MAPS_API_KEY:
        return "Error: Google Maps API key not configured. Add google_maps_api_key to add-on configuration."
    
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "mode": mode,
            "departure_time": "now",  # Get current traffic
            "key": config.GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] != 'OK':
            return f"Maps API error: {data.get('error_message', data['status'])}"
        
        if not data['rows'] or not data['rows'][0]['elements']:
            return "Could not calculate route between these locations."
        
        element = data['rows'][0]['elements'][0]
        
        if element['status'] != 'OK':
            return f"Route not found: {element.get('status')}"
        
        duration = element['duration']['text']
        distance = element['distance']['text']
        
        # Check if there's traffic data (duration_in_traffic)
        if 'duration_in_traffic' in element:
            duration_traffic = element['duration_in_traffic']['text']
            return f"Travel from {origin} to {destination} ({mode}):\nDistance: {distance}\nNormal time: {duration}\nCurrent traffic: {duration_traffic}"
        else:
            return f"Travel from {origin} to {destination} ({mode}):\nDistance: {distance}\nEstimated time: {duration}"
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return "Google Maps API error: Check that Distance Matrix API is enabled and API key is valid."
        return f"Maps API error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"Travel time error: {e}", exc_info=True)
        return f"Failed to get travel time: {e}"


def set_timer(seconds: int):
    """
    Set a timer for a specific number of seconds.
    Note: This runs in background. Timer completion notification depends on TTS integration.
    """
    def timer_thread():
        time.sleep(seconds)
        logger.info(f"[TIMER] Timer for {seconds} seconds finished!")
        # TODO: Trigger notification or TTS callback
        
    t = threading.Thread(target=timer_thread)
    t.daemon = True
    t.start()
    
    return f"Timer set for {seconds} seconds."


# ===== MEMORY FUNCTIONS =====

# Import memory singleton
from memory import Memory
_memory_instance = None

def _get_memory():
    """Get or create memory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = Memory()
    return _memory_instance

def save_preference(name: str, value: str):
    """
    Save a user preference or piece of information to memory.
    Use this when the user asks Jarvis to remember something.
    
    Args:
        name: The preference name/key (e.g., "favorite_color", "phone_number", "wife_name")
        value: The value to remember
        
    Returns:
        Confirmation message
    """
    try:
        memory = _get_memory()
        memory.set_preference(name, value)
        return f"Preference saved: {name} = {value}"
    except Exception as e:
        logger.error(f"Error saving preference: {e}", exc_info=True)
        return f"Failed to save preference: {e}"

def get_preference(name: str):
    """
    Retrieve a saved user preference from memory.
    Use this when the user asks what Jarvis remembers.
    
    Args:
        name: The preference name/key to retrieve
        
    Returns:
        The saved value, or message if not found
    """
    try:
        memory = _get_memory()
        value = memory.get_preference(name)
        if value is not None:
            return f"{name}: {value}"
        else:
            return f"No preference found for '{name}'"
    except Exception as e:
        logger.error(f"Error getting preference: {e}", exc_info=True)
        return f"Failed to get preference: {e}"

def list_all_preferences():
    """
    List all saved preferences.
    Use this when the user asks what Jarvis remembers.
    
    Returns:
        Dictionary of all saved preferences
    """
    try:
        memory = _get_memory()
        prefs = memory.get_all_preferences()
        if prefs:
            return f"Saved preferences: {prefs}"
        else:
            return "No preferences saved yet"
    except Exception as e:
        logger.error(f"Error listing preferences: {e}", exc_info=True)
        return f"Failed to list preferences: {e}"

def get_current_time():
    """
    Get the current date and time.
    Use this when the user asks about the current date, time, or needs calculations involving dates.
    
    Returns:
        Current date and time with timezone
    """
    from datetime import datetime
    import pytz
    
    # Get current time in UTC and local timezone
    now_utc = datetime.now(pytz.UTC)
    now_local = datetime.now()
    
    return f"Current date and time: {now_local.strftime('%A, %B %d, %Y at %I:%M %p')} (UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')})"

# ===== DEPRECATED/LEGACY =====

def get_tools():
    """Return list of all available tools for Gemini function calling."""
    tools = [
        # Home Assistant
        get_ha_state,
        search_ha_entities,
        control_home_assistant,
        get_last_interacted_entity,
        
        # Media
        play_music,
        
        # Media Management
        control_radarr,
        control_sonarr,
        
        # Knowledge & Search
        google_search,
        get_contextual_answer,
        get_weather,
        get_travel_time,
        
        # Memory
        save_preference,
        get_preference,
        list_all_preferences,
        
        # Utility
        get_current_time,
        set_timer,
    ]
    return tools
