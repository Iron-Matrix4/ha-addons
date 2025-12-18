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

    # Determine the correct service based on entity domain
    domain = entity_id.split('.')[0]
    
    # Buttons use press service, not turn_on/turn_off
    if domain == 'button':
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json",
        }
        service_data = {
            "entity_id": entity_id
        }
        url = f"{config.HA_URL}/api/services/button/press"
        try:
            response = requests.post(url, json=service_data, headers=headers, timeout=10)
            response.raise_for_status()
            _LAST_INTERACTED_ENTITY = entity_id
            return f"Pressed {entity_id} successfully."
        except Exception as e:
            return f"Failed to press {entity_id}: {e}"

    # Resolve the entity ID (handles Light/Switch mismatch fallback)
    resolved_id, was_resolved = _resolve_entity(entity_id)
    entity_id = resolved_id
    domain = entity_id.split(".")[0] # Re-evaluate domain in case of resolution
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

def get_appliance_status(appliance_name: str):
    """
    Get intelligent status of an appliance including time remaining, completion time, or current state.
    Automatically searches for relevant sensors that track completion, remaining time, or progress.
    
    Args:
        appliance_name: Name of the appliance (e.g., "washing machine", "dryer", "dishwasher")
    
    Returns:
        Status including time remaining if available
    """
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: Home Assistant connection not configured."
    
    try:
        # Search for all entities related to this appliance
        results = _search_ha_entities_raw(appliance_name)
        
        if not results:
            return f"No entities found for '{appliance_name}'"
        
        # Look for specific attributes that indicate time/completion
        time_keywords = ['remaining', 'finish', 'complete', 'end', 'duration', 'time_left', 'eta']
        status_keywords = ['status', 'state', 'program', 'cycle', 'phase']
        
        url = f"{config.HA_URL}/api/states"
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        all_entities = response.json()
        
        # Filter to our appliance's entities
        entity_ids = [r['entity_id'] for r in results]
        appliance_entities = [e for e in all_entities if e['entity_id'] in entity_ids]
        
        logger.debug(f"Found {len(appliance_entities)} entities for '{appliance_name}'")
        
        # Find time-related sensors
        time_info = []
        status_info = []
        power_info = None
        
        for entity in appliance_entities:
            entity_id = entity['entity_id']
            state = entity['state']
            attributes = entity.get('attributes', {})
            friendly_name = attributes.get('friendly_name', entity_id)
            
            # Check entity_id and attributes for time keywords
            entity_lower = entity_id.lower()
            
            # Skip power consumption sensors (they often have "end" but aren't what we want)
            if 'power' in entity_lower and 'consumption' in entity_lower:
                logger.debug(f"Skipping power consumption sensor: {entity_id}")
                continue
            
            # Prioritize keywords - check best matches first
            best_keywords = ['completion', 'remaining', 'finish', 'time_left', 'eta']
            ok_keywords = ['end', 'duration', 'complete']
            
            matched_keyword = None
            for keyword in best_keywords:
                if keyword in entity_lower:
                    matched_keyword = keyword
                    logger.debug(f"Matched BEST keyword '{keyword}' in {entity_id}")
                    break
            if not matched_keyword:
                for keyword in ok_keywords:
                    if keyword in entity_lower:
                        matched_keyword = keyword
                        logger.debug(f"Matched OK keyword '{keyword}' in {entity_id}")
                        break
            
            if matched_keyword:
                unit = attributes.get('unit_of_measurement', '')
                # More flexible time value check - accept numbers, datetime formats, timestamps
                if state and state not in ['unknown', 'unavailable', 'none', '']:
                    # Check if it's a valid time-related value
                    state_str = str(state).strip()
                    is_time_value = (
                        any(c.isdigit() for c in state_str) or  # Contains digits
                        'T' in state_str or  # ISO datetime format
                        '-' in state_str or  # Date format or negative number
                        ':' in state_str     # Time format
                    )
                    if is_time_value:
                        time_info.append(f"{friendly_name}: {state} {unit}".strip())
            
            # Check attributes for finish_at, end_time, etc. (but NOT friendly_name or device_class)
            skip_attrs = ['friendly_name', 'device_class', 'icon', 'unit_of_measurement']
            for attr_key, attr_val in attributes.items():
                if attr_key in skip_attrs:
                    continue
                attr_lower = attr_key.lower()
                if any(kw in attr_lower for kw in time_keywords):
                    # Only add if value looks meaningful (not None, not empty, has content)
                    if attr_val and str(attr_val).strip():
                        time_info.append(f"{attr_key.replace('_', ' ').title()}: {attr_val}")
            
            # Check for status/state sensors
            for keyword in status_keywords:
                if keyword in entity_lower and entity_id.startswith('sensor.'):
                    status_info.append(f"{friendly_name}: {state}")
                    break
            
            # Track power to see if it's running
            if 'power' in entity_lower and entity_id.startswith(('binary_sensor.', 'sensor.')):
                power_info = (friendly_name, state)
        
        # Build response
        output = [f"{appliance_name.title()} Status:"]
        
        if time_info:
            # Try to calculate relative time if we have a completion timestamp
            from datetime import datetime, timezone
            relative_time_str = None
            
            for info in time_info:
                # Look for ISO timestamp in the info
                if 'T' in info and 'Z' in info or '+' in info:
                    try:
                        # Extract timestamp from string like "Completion time: 2025-12-17T12:46:41+00:00"
                        timestamp_str = info.split(': ', 1)[1] if ': ' in info else info
                        timestamp_str = timestamp_str.strip()
                        
                        # Parse the timestamp
                        if timestamp_str.endswith('Z'):
                            finish_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            finish_time = datetime.fromisoformat(timestamp_str)
                        
                        # Calculate time remaining
                        now = datetime.now(timezone.utc)
                        remaining = finish_time - now
                        
                        # Convert to human-readable format
                        total_seconds = int(remaining.total_seconds())
                        if total_seconds > 0:
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            
                            if hours > 0:
                                relative_time_str = f"in {hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
                            elif minutes > 0:
                                relative_time_str = f"in {minutes} minute{'s' if minutes != 1 else ''}"
                            else:
                                relative_time_str = "less than a minute"
                        else:
                            relative_time_str = "already finished"
                        
                        break  # Found a valid timestamp, stop looking
                    except:
                        pass
            
            if relative_time_str:
                output.append(f"\n⏱️  {relative_time_str}")
            else:
                output.append("\nTime Remaining:")
                for info in time_info[:3]:  # Limit to 3 most relevant
                    # Filter out "Power Consumption End" from display
                    if 'power' not in info.lower() or 'consumption' not in info.lower():
                        output.append(f"  - {info}")
        
        if status_info:
            output.append("\nCurrent Status:")
            for info in status_info[:2]:
                output.append(f"  - {info}")
        
        if power_info and not time_info and not status_info:
            output.append(f"\nPower: {power_info[1]}")
        
        if len(output) == 1:  # Only header, no useful info found
            # Fall back to main entity state
            main_entity = appliance_entities[0] if appliance_entities else None
            if main_entity:
                state = main_entity['state']
                output.append(f"\nCurrent state: {state}")
                output.append(f"\nNote: No time remaining sensor found. Add a sensor that tracks completion time for better status updates.")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Appliance status error: {e}", exc_info=True)
        return f"Error getting status for {appliance_name}: {e}"

def get_person_location(person_name: str):
    """
    Get the location of a person from Home Assistant person entities.
    Looks up person.{name} and returns their current location/zone.
    
    Args:
        person_name: Name of the person (e.g., "John", "Sarah")
    """
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: Home Assistant connection not configured."
    
    try:
        # Try to find person entity by name
        # First try direct match: person.{lowercased_name}
        entity_id = f"person.{person_name.lower().replace(' ', '_')}"
        
        url = f"{config.HA_URL}/api/states/{entity_id}"
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json",
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 404:
            # Entity not found - try searching all person entities
            all_states_url = f"{config.HA_URL}/api/states"
            all_response = requests.get(all_states_url, headers=headers, timeout=5)
            all_response.raise_for_status()
            
            all_states = all_response.json()
            person_entities = [e for e in all_states if e['entity_id'].startswith('person.')]
            
            # Search by friendly name
            for entity in person_entities:
                friendly_name = entity.get('attributes', {}).get('friendly_name', '')
                if person_name.lower() in friendly_name.lower():
                    entity_id = entity['entity_id']
                    response = requests.get(f"{config.HA_URL}/api/states/{entity_id}", headers=headers, timeout=5)
                    break
            else:
                return f"Could not find a person entity for '{person_name}'. Make sure they have a person entity in Home Assistant."
        
        response.raise_for_status()
        state_data = response.json()
        
        location = state_data['state']
        friendly_name = state_data.get('attributes', {}).get('friendly_name', person_name)
        
        # Get additional context
        source = state_data.get('attributes', {}).get('source', '')
        latitude = state_data.get('attributes', {}).get('latitude')
        longitude = state_data.get('attributes', {}).get('longitude')
        
        # Format response based on location
        if location == "home":
            return f"{friendly_name} is at home, Sir."
        elif location == "not_home":
            if latitude and longitude:
                return f"{friendly_name} is away from home, Sir. Last known coordinates: {latitude}, {longitude}"
            return f"{friendly_name} is away from home, Sir."
        else:
            # Named zone
            return f"{friendly_name} is at {location}, Sir."
            
    except requests.exceptions.HTTPError as e:
        return f"Failed to get location for {person_name}: {e}"
    except Exception as e:
        logger.error(f"Person location error: {e}", exc_info=True)
        return f"Error getting person location: {e}"

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
        logger.debug(f"Playing {uri} on {target_entity} via Spotcast")
        
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

# ===== QBITTORRENT INTEGRATION =====

def query_qbittorrent(query_type: str):
    """
    Query qBittorrent for torrent status and download information.
    
    Args:
        query_type: Type of query:
            - "status" - Is qBittorrent running?
            - "stats" - Torrent counts (downloading, seeding, paused)
            - "speed" - Current download/upload speed
            - "downloading" - What's actively downloading?
            - "completed" - Recently completed torrents
    """
    if not config.QBITTORRENT_URL:
        return "Error: qBittorrent URL not configured."
    
    try:
        # Login if credentials provided
        session = requests.Session()
        if config.QBITTORRENT_USERNAME and config.QBITTORRENT_PASSWORD:
            login_url = f"{config.QBITTORRENT_URL}/api/v2/auth/login"
            login_data = {
                "username": config.QBITTORRENT_USERNAME,
                "password": config.QBITTORRENT_PASSWORD
            }
            login_response = session.post(login_url, data=login_data, timeout=5)
            if "Fails" in login_response.text or login_response.status_code != 200:
                return "Error: qBittorrent authentication failed."
        
        if query_type == "status":
            # Check if qBittorrent is responding AND get connection status
            url = f"{config.QBITTORRENT_URL}/api/v2/app/version"
            response = session.get(url, timeout=5)
            response.raise_for_status()
            version = response.text
            
            # Also get connection status
            transfer_url = f"{config.QBITTORRENT_URL}/api/v2/transfer/info"
            transfer_response = session.get(transfer_url, timeout=5)
            transfer_response.raise_for_status()
            transfer_info = transfer_response.json()
            
            connection_status = transfer_info.get('connection_status', 'unknown')
            
            # Format connection status
            if connection_status == 'connected':
                status_msg = "Connected and working"
            elif connection_status == 'firewalled':
                status_msg = "Connected but firewalled (incoming connections blocked)"
            elif connection_status == 'disconnected':
                status_msg = "DISCONNECTED - Check VPN! Downloads will not work."
            else:
                status_msg = f"Status: {connection_status}"
            
            return f"qBittorrent is running (v{version}). Connection: {status_msg}"
        
        elif query_type == "stats":
            # Get torrent counts
            url = f"{config.QBITTORRENT_URL}/api/v2/torrents/info"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            torrents = response.json()
            
            downloading = sum(1 for t in torrents if t['state'] in ['downloading', 'stalledDL', 'metaDL', 'forcedDL'])
            seeding = sum(1 for t in torrents if t['state'] in ['uploading', 'stalledUP', 'forcedUP'])
            paused = sum(1 for t in torrents if 'paused' in t['state'].lower())
            total = len(torrents)
            
            return f"qBittorrent Stats: {total} torrents total, {downloading} downloading, {seeding} seeding, {paused} paused"
        
        elif query_type == "speed":
            # Get transfer info
            url = f"{config.QBITTORRENT_URL}/api/v2/transfer/info"
            response = session.get(url, timeout=5)
            response.raise_for_status()
            info = response.json()
            
            dl_speed = info.get('dl_info_speed', 0) / 1024 / 1024  # Convert to MB/s
            up_speed = info.get('up_info_speed', 0) / 1024 / 1024
            
            return f"qBittorrent Speed: ↓ {dl_speed:.1f} MB/s, ↑ {up_speed:.1f} MB/s"
        
        elif query_type == "downloading":
            # Get active downloads
            url = f"{config.QBITTORRENT_URL}/api/v2/torrents/info"
            params = {"filter": "downloading"}
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            torrents = response.json()
            
            if not torrents:
                return "No torrents currently downloading."
            
            output = [f"Downloading ({len(torrents)} torrents):"]
            for t in torrents[:5]:
                name = t.get('name', 'Unknown')[:50]
                progress = t.get('progress', 0) * 100
                eta = t.get('eta', 0)
                
                if eta > 0 and eta < 86400 * 30:  # Less than 30 days
                    hours, remainder = divmod(eta, 3600)
                    minutes = remainder // 60
                    eta_str = f"{int(hours)}h {int(minutes)}m"
                else:
                    eta_str = "unknown"
                
                output.append(f"- {name}: {progress:.0f}% (ETA: {eta_str})")
            
            return "\n".join(output)
        
        elif query_type == "completed":
            # Get recent completed
            url = f"{config.QBITTORRENT_URL}/api/v2/torrents/info"
            params = {"filter": "completed", "sort": "completion_on", "reverse": "true"}
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            torrents = response.json()
            
            if not torrents:
                return "No completed torrents found."
            
            output = ["Recently Completed:"]
            for t in torrents[:5]:
                name = t.get('name', 'Unknown')[:50]
                size = t.get('size', 0) / 1024 / 1024 / 1024  # GB
                output.append(f"- {name} ({size:.1f} GB)")
            
            return "\n".join(output)
        
        else:
            return f"Unknown query type: {query_type}. Supported: status, stats, speed, downloading, completed"
    
    except requests.exceptions.ConnectionError:
        return "qBittorrent is not responding. It may be offline or the URL is incorrect."
    except requests.exceptions.Timeout:
        return "qBittorrent connection timed out."
    except Exception as e:
        return f"qBittorrent error: {e}"


# ===== PROWLARR INTEGRATION =====

def query_prowlarr(query_type: str):
    """
    Query Prowlarr for indexer status and information.
    
    Args:
        query_type: Type of query:
            - "status" - Is Prowlarr running?
            - "stats" - Indexer counts (total, working, failing)
            - "indexers" - List indexer status
    """
    if not config.PROWLARR_URL or not config.PROWLARR_API_KEY:
        return "Error: Prowlarr URL or API key not configured."
    
    headers = {
        "X-Api-Key": config.PROWLARR_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        if query_type == "status":
            url = f"{config.PROWLARR_URL}/api/v1/system/status"
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            status = response.json()
            
            version = status.get('version', 'Unknown')
            return f"Prowlarr is running. Version: {version}"
        
        elif query_type in ["stats", "indexers"]:
            url = f"{config.PROWLARR_URL}/api/v1/indexer"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            indexers = response.json()
            
            total = len(indexers)
            enabled = sum(1 for i in indexers if i.get('enable', False))
            
            if query_type == "stats":
                return f"Prowlarr Stats: {total} indexers configured, {enabled} enabled"
            
            else:  # indexers
                if not indexers:
                    return "No indexers configured in Prowlarr."
                
                output = [f"Indexers ({total} total):"]
                for idx in indexers[:10]:
                    name = idx.get('name', 'Unknown')
                    enabled_status = "✓" if idx.get('enable', False) else "✗"
                    output.append(f"- {enabled_status} {name}")
                
                return "\n".join(output)
        
        else:
            return f"Unknown query type: {query_type}. Supported: status, stats, indexers"
    
    except requests.exceptions.ConnectionError:
        return "Prowlarr is not responding. It may be offline or the URL is incorrect."
    except requests.exceptions.Timeout:
        return "Prowlarr connection timed out."
    except Exception as e:
        return f"Prowlarr error: {e}"


# ===== VPN STATUS CHECK =====

def check_vpn_status():
    """
    Check if VPN is connected on the download VM by verifying qBittorrent's connectivity.
    Compares qBittorrent's external IP against home WAN IP from UniFi sensor.
    """
    try:
        # First, try to get external IP through qBittorrent's host (the VM with VPN)
        vm_ip = None
        qbit_status = "unknown"
        
        if config.QBITTORRENT_URL:
            try:
                # Try to login and check qBit status
                session = requests.Session()
                if config.QBITTORRENT_USERNAME and config.QBITTORRENT_PASSWORD:
                    login_url = f"{config.QBITTORRENT_URL}/api/v2/auth/login"
                    login_data = {
                        "username": config.QBITTORRENT_USERNAME,
                        "password": config.QBITTORRENT_PASSWORD
                    }
                    session.post(login_url, data=login_data, timeout=5)
                
                # Check if qBit is connected and can download
                transfer_url = f"{config.QBITTORRENT_URL}/api/v2/transfer/info"
                transfer_response = session.get(transfer_url, timeout=5)
                
                if transfer_response.status_code == 200:
                    transfer_info = transfer_response.json()
                    connection_status = transfer_info.get('connection_status', 'unknown')
                    
                    if connection_status in ['connected', 'firewalled']:
                        qbit_status = "connected"
                    elif connection_status == 'disconnected':
                        qbit_status = "disconnected"
                    else:
                        qbit_status = connection_status
                        
            except requests.exceptions.ConnectionError:
                return "⚠️ Cannot reach qBittorrent. The VM or qBittorrent may be offline."
            except Exception as e:
                qbit_status = f"error: {e}"
        
        # Get home WAN IP from UniFi sensor for comparison
        home_ip = None
        if config.HA_URL and config.HA_TOKEN:
            try:
                sensor_entity = config.UNIFI_WAN_SENSOR
                url = f"{config.HA_URL}/api/states/{sensor_entity}"
                headers = {
                    "Authorization": f"Bearer {config.HA_TOKEN}",
                    "Content-Type": "application/json"
                }
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    home_ip = response.json().get('state', '')
            except Exception:
                pass
        
        # Get external IP from HA's perspective (for reference)
        ha_ip = None
        try:
            ext_ip_response = requests.get("https://api.ipify.org?format=json", timeout=5)
            ext_ip_response.raise_for_status()
            ha_ip = ext_ip_response.json().get('ip', 'Unknown')
        except Exception:
            pass
        
        # Do geo lookup for HA's current IP
        location = "Unknown"
        if ha_ip:
            try:
                geo_response = requests.get(f"http://ip-api.com/json/{ha_ip}?fields=status,country,city,isp", timeout=5)
                if geo_response.status_code == 200:
                    geo_data = geo_response.json()
                    if geo_data.get('status') == 'success':
                        city = geo_data.get('city', 'Unknown')
                        country = geo_data.get('country', 'Unknown')
                        isp = geo_data.get('isp', 'Unknown')
                        location = f"{city}, {country} ({isp})"
            except Exception:
                pass
        
        # Build response based on qBit status
        if qbit_status == "connected":
            if home_ip and ha_ip:
                if ha_ip == home_ip:
                    # HA shows home IP, so check if qBit is connected (VPN is separate)
                    return f"✅ VPN appears connected. qBittorrent is online and connected. Home IP: {home_ip}. HA IP: {ha_ip} (Location: {location})"
                else:
                    return f"✅ VPN connected. qBittorrent is online. Current HA IP: {ha_ip}. Location: {location}"
            else:
                return f"✅ qBittorrent is connected and online. VPN likely working. (Could not verify home IP)"
        elif qbit_status == "disconnected":
            return f"⚠️ VPN may be DOWN! qBittorrent reports disconnected status. Check IPVanish on the VM."
        else:
            return f"VPN status uncertain. qBittorrent status: {qbit_status}. Home IP: {home_ip or 'unknown'}"
    
    except Exception as e:
        return f"VPN check error: {e}"


# ===== UNIFI NETWORK INTEGRATION =====

def query_unifi_network(query_type: str):
    """
    Query UniFi network information from Home Assistant sensors.
    
    Args:
        query_type: Type of query:
            - "wan_ip" - Current WAN IP address
            - "devices" - Number of connected devices
            - "bandwidth" - Current bandwidth usage (if available)
            - "uptime" - Gateway uptime
            - "stats" - General network statistics
    """
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: Home Assistant connection not configured."
    
    headers = {
        "Authorization": f"Bearer {config.HA_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Common UniFi sensor entity patterns
        sensor_patterns = {
            "wan_ip": ["sensor.unifi_gateway_wan_ip", "sensor.udm_wan_ip", "sensor.usg_wan_ip"],
            "devices": ["sensor.unifi_network_clients", "sensor.unifi_devices", "sensor.udm_connected_clients"],
            "uptime": ["sensor.unifi_gateway_uptime", "sensor.udm_uptime", "sensor.usg_uptime"],
            "download": ["sensor.unifi_network_wan_download", "sensor.udm_wan_download"],
            "upload": ["sensor.unifi_network_wan_upload", "sensor.udm_wan_upload"],
        }
        
        def get_sensor_value(patterns):
            """Try multiple sensor patterns and return first found."""
            for pattern in patterns:
                try:
                    url = f"{config.HA_URL}/api/states/{pattern}"
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        state = data.get('state', 'unknown')
                        unit = data.get('attributes', {}).get('unit_of_measurement', '')
                        friendly_name = data.get('attributes', {}).get('friendly_name', pattern)
                        if state and state != 'unavailable' and state != 'unknown':
                            return state, unit, friendly_name
                except Exception:
                    continue
            return None, None, None
        
        if query_type == "wan_ip":
            state, _, name = get_sensor_value(sensor_patterns["wan_ip"])
            if state:
                # Also do geo lookup
                location = ""
                try:
                    geo_response = requests.get(f"http://ip-api.com/json/{state}?fields=status,country,city,isp", timeout=5)
                    if geo_response.status_code == 200:
                        geo_data = geo_response.json()
                        if geo_data.get('status') == 'success':
                            location = f" (Location: {geo_data.get('city', 'Unknown')}, {geo_data.get('country', 'Unknown')})"
                except Exception:
                    pass
                return f"Your WAN IP is {state}{location}"
            return "Could not find UniFi WAN IP sensor. Make sure the UniFi integration is set up."
        
        elif query_type == "devices":
            state, unit, name = get_sensor_value(sensor_patterns["devices"])
            if state:
                return f"There are {state} devices connected to your network."
            return "Could not find UniFi device count sensor."
        
        elif query_type == "uptime":
            state, unit, name = get_sensor_value(sensor_patterns["uptime"])
            if state:
                # Try to format nicely
                try:
                    # If it's in seconds, convert to readable
                    seconds = float(state)
                    days = int(seconds // 86400)
                    hours = int((seconds % 86400) // 3600)
                    minutes = int((seconds % 3600) // 60)
                    uptime_str = f"{days} days, {hours} hours, {minutes} minutes"
                    return f"Gateway uptime: {uptime_str}"
                except ValueError:
                    return f"Gateway uptime: {state} {unit}"
            return "Could not find UniFi uptime sensor."
        
        elif query_type == "bandwidth":
            dl_state, dl_unit, _ = get_sensor_value(sensor_patterns["download"])
            up_state, up_unit, _ = get_sensor_value(sensor_patterns["upload"])
            
            if dl_state or up_state:
                parts = []
                if dl_state:
                    parts.append(f"↓ {dl_state} {dl_unit}")
                if up_state:
                    parts.append(f"↑ {up_state} {up_unit}")
                return f"Current bandwidth: {', '.join(parts)}"
            return "Could not find UniFi bandwidth sensors."
        
        elif query_type == "stats":
            # Get all available stats
            results = []
            
            wan_ip, _, _ = get_sensor_value(sensor_patterns["wan_ip"])
            if wan_ip:
                results.append(f"WAN IP: {wan_ip}")
            
            devices, _, _ = get_sensor_value(sensor_patterns["devices"])
            if devices:
                results.append(f"Connected devices: {devices}")
            
            uptime, unit, _ = get_sensor_value(sensor_patterns["uptime"])
            if uptime:
                try:
                    seconds = float(uptime)
                    days = int(seconds // 86400)
                    hours = int((seconds % 86400) // 3600)
                    results.append(f"Uptime: {days}d {hours}h")
                except ValueError:
                    results.append(f"Uptime: {uptime}")
            
            if results:
                return "UniFi Network Stats:\n" + "\n".join(f"- {r}" for r in results)
            return "Could not retrieve UniFi network stats. Check that the UniFi integration is configured."
        
        else:
            return f"Unknown query type: {query_type}. Supported: wan_ip, devices, bandwidth, uptime, stats"
    
    except Exception as e:
        return f"UniFi query error: {e}"


# ===== UNIFI CONTROLLER API (ADVANCED) =====

def _get_unifi_session():
    """
    Create authenticated session with UniFi Controller.
    Supports both API token (preferred) and username/password auth.
    """
    if not config.UNIFI_CONTROLLER_URL:
        return None, "UniFi Controller URL not configured"
    
    session = requests.Session()
    # Disable SSL warnings for self-signed certs (common with UniFi)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.verify = False
    
    try:
        # Try API token first (recommended for UniFi OS / Cloud Gateway Max)
        if config.UNIFI_CONTROLLER_API_TOKEN:
            # Cloud Gateway Max uses X-API-KEY header
            session.headers.update({
                "X-API-KEY": config.UNIFI_CONTROLLER_API_TOKEN,
                "Content-Type": "application/json"
            })
            logger.info("Using UniFi API token authentication")
            return session, None
        
        # Fall back to username/password
        elif config.UNIFI_CONTROLLER_USERNAME and config.UNIFI_CONTROLLER_PASSWORD:
            login_url = f"{config.UNIFI_CONTROLLER_URL}/api/auth/login"
            login_data = {
                "username": config.UNIFI_CONTROLLER_USERNAME,
                "password": config.UNIFI_CONTROLLER_PASSWORD
            }
            
            response = session.post(login_url, json=login_data, timeout=10)
            response.raise_for_status()
            
            # UniFi OS uses token in response
            if "x-csrf-token" in response.headers:
                session.headers.update({
                    "X-CSRF-Token": response.headers["x-csrf-token"]
                })
            
            logger.info("UniFi session authenticated with username/password")
            return session, None
        
        else:
            return None, "UniFi Controller credentials not configured (need API token or username/password)"
    
    except Exception as e:
        logger.error(f"UniFi authentication error: {e}", exc_info=True)
        return None, f"Failed to authenticate with UniFi Controller: {e}"


def query_unifi_controller(query_type: str, subnet: str = "", client_id: str = ""):
    """
    Advanced UniFi Controller queries for network information not available through HA integration.
    
    Args:
        query_type: Type of query:
            - "dhcp_leases" - Show active DHCP leases
            - "dhcp_stats" - DHCP statistics summary
            - "next_ip" - Find next available IP in subnet (requires subnet parameter)
            - "clients_active" - List active clients
            - "clients_count" - Count of connected clients
            - "clients_bandwidth" - Clients using most bandwidth
            - "network_info" - Network configuration overview
            - "firewall_rules" - Firewall rules summary
            - "port_forwarding" - Port forwarding rules
            - "device_info" - UniFi device information (USG/UDM stats)
        subnet: Optional subnet for next_ip query (e.g., "192.168.1.0/24")
    """
    session, error = _get_unifi_session()
    if error:
        return f"Error: {error}"
    
    site_id = config.UNIFI_SITE_ID or "default"
    base_url = config.UNIFI_CONTROLLER_URL.rstrip('/')
    
    try:
        if query_type == "dhcp_leases":
            # Get active clients (includes DHCP info) - Cloud Gateway Max API v2
            url = f"{base_url}/proxy/network/v2/api/site/{site_id}/clients/active"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return "No active clients/DHCP leases found."
            
            # Cloud Gateway Max returns array directly
            leases = data if isinstance(data, list) else data.get('data', [])
            output = [f"Active DHCP Leases ({len(leases)} total):"]
            
            for lease in leases[:20]:  # Limit to 20 for voice output
                hostname = lease.get('hostname') or lease.get('name', 'Unknown')
                ip = lease.get('ip') or lease.get('fixed_ip', 'N/A')
                mac = lease.get('mac', 'N/A')
                output.append(f"- {hostname}: {ip} ({mac})")
            
            if len(leases) > 20:
                output.append(f"... and {len(leases) - 20} more")
            
            return "\n".join(output)
        
        elif query_type == "dhcp_stats":
            # Use same endpoint as dhcp_leases - Cloud Gateway Max API v2
            url = f"{base_url}/proxy/network/v2/api/site/{site_id}/clients/active"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            leases = data if isinstance(data, list) else data.get('data', [])
            total = len(leases)
            
            return f"Total active DHCP leases: {total}"
        
        elif query_type == "network_stats":
            # Get comprehensive stats for a specific network by name
            if not subnet:  # Using subnet parameter to pass network name
                return "Error: network name required (e.g., 'Main-Network')"
            
            import ipaddress
            
            # Get network configuration
            url_net = f"{base_url}/proxy/network/api/s/{site_id}/rest/networkconf"
            response_net = session.get(url_net, timeout=10, verify=False)
            response_net.raise_for_status()
            net_data = response_net.json()
            
            # Find the network by name
            network_config = None
            for net in net_data.get('data', []):
                net_name = net.get('name', '')
                if subnet.lower() == net_name.lower() or subnet.lower().replace('-', ' ') == net_name.replace('-', ' ').lower():
                    network_config = net
                    break
            
            if not network_config:
                return f"Network '{subnet}' not found. Check network name in UniFi controller."
            
            # Extract network details
            name = network_config.get('name', 'Unknown')
            net_subnet = network_config.get('ip_subnet') or f"{network_config.get('network')}/{network_config.get('networkgroup', 24)}"
            vlan_id = network_config.get('vlan') or network_config.get('vlan_id', 'Default')
            dhcp_start = network_config.get('dhcpd_start', 'N/A')
            dhcp_end = network_config.get('dhcpd_stop', 'N/A')
            dhcp_enabled = network_config.get('dhcpd_enabled', False)
            
            # Get clients from this network using /stat/sta (has network names)
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/sta"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            clients_data = data.get('data', [])
            network_obj = ipaddress.IPv4Network(net_subnet, strict=False)
            
            # Filter clients by network name and collect stats
            network_clients = []
            total_rx = 0
            total_tx = 0
            wired_count = 0
            wireless_count = 0
            used_ips = set()
            
            for client in clients_data:
                if client.get('last_connection_network_name') == name:
                    network_clients.append(client)
                    total_rx += client.get('rx_bytes', 0)
                    total_tx += client.get('tx_bytes', 0)
                    
                    if client.get('is_wired', False):
                        wired_count += 1
                    else:
                        wireless_count += 1
                    
                    # Track used IPs
                    ip_str = client.get('last_ip')
                    if ip_str:
                        try:
                            used_ips.add(ipaddress.IPv4Address(ip_str))
                        except:
                            pass
            
            client_count = len(network_clients)
            
            # Find next available IP if DHCP is enabled
            next_ip = "N/A"
            if dhcp_enabled and dhcp_start != 'N/A':
                dhcp_start_ip = ipaddress.IPv4Address(dhcp_start)
                dhcp_end_ip = ipaddress.IPv4Address(dhcp_end)
                
                for ip in network_obj.hosts():
                    if ip < dhcp_start_ip or ip > dhcp_end_ip:
                        continue
                    if ip not in used_ips:
                        next_ip = str(ip)
                        break
            
            # Format bandwidth
            def format_bytes(bytes_val):
                if bytes_val >= 1e9:
                    return f"{bytes_val / 1e9:.2f} GB"
                elif bytes_val >= 1e6:
                    return f"{bytes_val / 1e6:.2f} MB"
                elif bytes_val >= 1e3:
                    return f"{bytes_val / 1e3:.2f} KB"
                return f"{bytes_val} B"
            
            # Build response
            output = [
                f"Network: {name}",
                f"Subnet: {net_subnet}",
                f"VLAN ID: {vlan_id}",
                f"DHCP: {'Enabled' if dhcp_enabled else 'Disabled'}",
            ]
            
            if dhcp_enabled:
                output.append(f"DHCP Range: {dhcp_start} - {dhcp_end}")
            
            output.extend([
                f"Active Clients: {client_count} (Wired: {wired_count}, Wireless: {wireless_count})",
                f"Total RX: {format_bytes(total_rx)}",
                f"Total TX: {format_bytes(total_tx)}",
                f"Next Available IP: {next_ip}"
            ])
            
            return "\n".join(output)
        
        elif query_type == "next_ip":
            # Find next available IP in subnet
            if not subnet:
                return "Error: subnet parameter required for next_ip query (e.g., '192.168.1.0/24' or network name like 'Main-Network')"
            
            import ipaddress
            
            # Get network config first to resolve names and get DHCP ranges
            url_net = f"{base_url}/proxy/network/api/s/{site_id}/rest/networkconf"
            response_net = session.get(url_net, timeout=10, verify=False)
            response_net.raise_for_status()
            net_data = response_net.json()
            
            # Check if subnet is a name instead of CIDR
            resolved_subnet = None
            dhcp_start = None
            dhcp_end = None
            
            # First, try to match as network name
            for net in net_data.get('data', []):
                net_name = net.get('name', '').lower()
                if subnet.lower() == net_name or subnet.lower().replace('-', ' ') == net_name.replace('-', ' '):
                    resolved_subnet = net.get('ip_subnet') or f"{net.get('network')}/{net.get('networkgroup', 24)}"
                    dhcp_start = net.get('dhcpd_start')
                    dhcp_end = net.get('dhcpd_stop')
                    logger.info(f"Resolved network name '{subnet}' to {resolved_subnet}")
                    break
            
            # If not found as name, try as CIDR and find matching network
            if not resolved_subnet:
                try:
                    # Validate as CIDR
                    test_network = ipaddress.IPv4Network(subnet, strict=False)
                    resolved_subnet = str(test_network)
                    
                    # Find DHCP range for this subnet - normalize both for comparison
                    for net in net_data.get('data', []):
                        net_subnet = net.get('ip_subnet') or f"{net.get('network')}/{net.get('networkgroup', 24)}"
                        # Normalize the network subnet for comparison
                        try:
                            net_normalized = str(ipaddress.IPv4Network(net_subnet, strict=False))
                            if net_normalized == resolved_subnet:
                                dhcp_start = net.get('dhcpd_start')
                                dhcp_end = net.get('dhcpd_stop')
                                logger.info(f"Matched subnet {resolved_subnet}, DHCP: {dhcp_start} - {dhcp_end}")
                                break
                        except:
                            pass
                except ValueError:
                    return f"Invalid subnet format. Use CIDR notation (e.g., '192.168.1.0/24') or network name (e.g., 'IoT')"
            
            # Parse the resolved subnet
            try:
                network = ipaddress.IPv4Network(resolved_subnet, strict=False)
            except ValueError as e:
                return f"Invalid subnet format: {e}"
            
            if not dhcp_start or not dhcp_end:
                logger.warning(f"No DHCP range found for {subnet}")
                # Fall back to scanning whole subnet
                dhcp_start_ip = list(network.hosts())[10]  # Start at .11 as fallback
                dhcp_end_ip = list(network.hosts())[-2]
            else:
                dhcp_start_ip = ipaddress.IPv4Address(dhcp_start)
                dhcp_end_ip = ipaddress.IPv4Address(dhcp_end)
                logger.info(f"DHCP range: {dhcp_start} - {dhcp_end}")
            
            # Get all active clients (use v2 endpoint that works)
            url = f"{base_url}/proxy/network/v2/api/site/{site_id}/clients/active"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            # Get used IPs
            used_ips = set()
            clients = data if isinstance(data, list) else data.get('data', [])
            for client in clients:
                ip_str = client.get('ip')
                if ip_str:
                    try:
                        ip = ipaddress.IPv4Address(ip_str)
                        if ip in network:
                            used_ips.add(ip)
                    except:
                        pass
            
            # Find next available IP within DHCP range
            for ip in network.hosts():
                if ip < dhcp_start_ip or ip > dhcp_end_ip:
                    continue  # Skip IPs outside DHCP range
                    
                if ip not in used_ips:
                    return f"Next available IP in {subnet}: {ip}"
            
            return f"No available IPs in DHCP range ({dhcp_start} - {dhcp_end})"
        
        elif query_type == "clients_active":
            # Get active clients
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/sta"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                return "No active clients found."
            
            clients = data['data']
            output = [f"Active Clients ({len(clients)} total):"]
            
            for client in clients[:15]:  # Limit for voice
                hostname = client.get('hostname') or client.get('name', 'Unknown')
                ip = client.get('ip', 'N/A')
                is_wired = client.get('is_wired', False)
                connection = "Wired" if is_wired else "Wireless"
                output.append(f"- {hostname}: {ip} ({connection})")
            
            if len(clients) > 15:
                output.append(f"... and {len(clients) - 15} more")
            
            return "\n".join(output)
        
        elif query_type == "clients_count":
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/sta"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            clients = data.get('data', [])
            wired = sum(1 for c in clients if c.get('is_wired', False))
            wireless = len(clients) - wired
            
            return f"Network Clients:\n- Total: {len(clients)}\n- Wired: {wired}\n- Wireless: {wireless}"
        
        elif query_type == "clients_bandwidth":
            # Get clients and sort by bandwidth usage
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/sta"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                return "No active clients found."
            
            clients = data['data']
            # Sort by total bandwidth (tx + rx)
            clients_sorted = sorted(
                clients,
                key=lambda c: c.get('tx_bytes', 0) + c.get('rx_bytes', 0),
                reverse=True
            )
            
            output = ["Top Bandwidth Users:"]
            for client in clients_sorted[:10]:
                hostname = client.get('hostname') or client.get('name', 'Unknown')
                tx_bytes = client.get('tx_bytes', 0)
                rx_bytes = client.get('rx_bytes', 0)
                total_mb = (tx_bytes + rx_bytes) / (1024 * 1024)
                output.append(f"- {hostname}: {total_mb:.1f} MB")
            
            return "\n".join(output)
        
        elif query_type == "network_info":
            # Get network configuration - Use legacy API (v2 doesn't work for this)
            url = f"{base_url}/proxy/network/api/s/{site_id}/rest/networkconf"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                return "No network configuration found."
            
            networks = data['data']
            output = [f"Network Configuration ({len(networks)} networks):"]
            
            for net in networks[:10]:  # Limit output
                name = net.get('name', 'Unknown')
                purpose = net.get('purpose', 'corporate')
                subnet = net.get('ip_subnet') or f"{net.get('network', 'N/A')}/{net.get('networkgroup', 24)}"
                vlan = net.get('vlan') or net.get('vlan_id', 'Default')
                dhcp_enabled = net.get('dhcpd_enabled', False)
                output.append(f"- {name} ({purpose}): {subnet}, VLAN {vlan}, DHCP: {'Yes' if dhcp_enabled else 'No'}")
            
            return "\n".join(output)
        
        elif query_type == "wan_ip":
            # Get WAN IP from health status - this is where Cloud Gateway Max stores it
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/health"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                return "Could not retrieve WAN IP from UniFi Controller"
            
            # Find the WAN subsystem in health data
            for subsystem in data['data']:
                if subsystem.get('subsystem') == 'wan':
                    wan_ip = subsystem.get('wan_ip')
                    if wan_ip:
                        logger.info(f"Found WAN IP: {wan_ip}")
                        return f"WAN IP: {wan_ip}"
            
            logger.warning("No WAN subsystem found in health data")
            return "Could not retrieve WAN IP from UniFi Controller"
        
        elif query_type == "firewall_rules":
            # Get firewall rules
            url = f"{base_url}/proxy/network/api/s/{site_id}/rest/firewallrule"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                return "No firewall rules configured."
            
            rules = data['data']
            enabled_rules = [r for r in rules if r.get('enabled', False)]
            
            output = [f"Firewall Rules ({len(enabled_rules)} enabled, {len(rules)} total):"]
            
            for rule in enabled_rules[:10]:
                name = rule.get('name', 'Unnamed')
                action = rule.get('action', 'N/A')
                protocol = rule.get('protocol', 'all')
                output.append(f"- {name}: {action} {protocol}")
            
            if len(enabled_rules) > 10:
                output.append(f"... and {len(enabled_rules) - 10} more")
            
            return "\n".join(output)
        
        elif query_type == "port_forwarding":
            # Get port forwarding rules
            url = f"{base_url}/proxy/network/api/s/{site_id}/rest/portforward"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                return "No port forwarding rules configured."
            
            rules = data['data']
            enabled_rules = [r for r in rules if r.get('enabled', False)]
            
            output = [f"Port Forwarding Rules ({len(enabled_rules)} enabled):"]
            
            for rule in enabled_rules:
                name = rule.get('name', 'Unnamed')
                dst_port = rule.get('dst_port', 'N/A')
                fwd_port = rule.get('fwd_port', dst_port)
                fwd_ip = rule.get('fwd', 'N/A')
                protocol = rule.get('proto', 'tcp')
                output.append(f"- {name}: {dst_port} → {fwd_ip}:{fwd_port} ({protocol})")
            
            if not enabled_rules:
                return "No active port forwarding rules."
            
            return "\n".join(output)
        
        elif query_type == "device_info":
            # Get UniFi device information (USG/UDM/switches/APs)
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/device"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                return "No UniFi devices found."
            
            devices = data['data']
            output = [f"UniFi Devices ({len(devices)} total):"]
            
            for device in devices:
                name = device.get('name', 'Unknown')
                model = device.get('model', 'N/A')
                version = device.get('version', 'N/A')
                state = device.get('state', 0)
                status = "Online" if state == 1 else "Offline"
                uptime = device.get('uptime', 0)
                uptime_hours = uptime // 3600
                output.append(f"- {name} ({model}): {status}, Uptime: {uptime_hours}h, v{version}")
            
            return "\n".join(output)
        
        elif query_type == "client_signal":
            # Get signal strength for a specific client
            if not client_id:
                return "Error: client_id required (hostname, IP, or MAC)"
            
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/sta"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            clients = response.json().get('data', [])
            
            # Search for client by hostname, IP, or MAC
            client_id_lower = client_id.lower()
            found_client = None
            for client in clients:
                if (client_id_lower in (client.get('hostname', '').lower(), 
                                       client.get('last_ip', '').lower(),
                                       client.get('mac', '').lower())):
                    found_client = client
                    break
            
            if not found_client:
                return f"Client '{client_id}' not found in network"
            
            hostname = found_client.get('hostname', 'Unknown')
            signal = found_client.get('signal', 'N/A')
            rssi = found_client.get('rssi', 'N/A')
            noise = found_client.get('noise', 'N/A')
            channel = found_client.get('channel', 'N/A')
            is_wired = found_client.get('is_wired', False)
            
            if is_wired:
                return f"{hostname}: Wired connection (no wireless signal)"
            
            return f"{hostname} Signal:\n- Signal: {signal} dBm\n- RSSI: {rssi}\n- Noise: {noise} dBm\n- Channel: {channel}"
        
        elif query_type == "client_details":
            # Get full details for a specific client
            if not client_id:
                return "Error: client_id required (hostname, IP, or MAC)"
            
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/sta"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            clients = response.json().get('data', [])
            
            # Search for client
            client_id_lower = client_id.lower()
            found_client = None
            for client in clients:
                if (client_id_lower in (client.get('hostname', '').lower(), 
                                       client.get('last_ip', '').lower(),
                                       client.get('mac', '').lower())):
                    found_client = client
                    break
            
            if not found_client:
                return f"Client '{client_id}' not found in network"
            
            # Format uptime
            uptime = found_client.get('uptime', 0)
            uptime_hours = uptime // 3600
            uptime_mins = (uptime % 3600) // 60
            
            # Format bandwidth
            rx_gb = found_client.get('rx_bytes', 0) / 1e9
            tx_gb = found_client.get('tx_bytes', 0) / 1e9
            
            output = [
                f"Client: {found_client.get('hostname', 'Unknown')}",
                f"IP: {found_client.get('last_ip', 'N/A')}",
                f"MAC: {found_client.get('mac', 'N/A')}",
                f"Network: {found_client.get('last_connection_network_name', 'Unknown')}",
                f"Connection: {'Wired' if found_client.get('is_wired') else 'Wireless'}",
                f"Uptime: {uptime_hours}h {uptime_mins}m",
                f"Bandwidth: RX {rx_gb:.2f} GB, TX {tx_gb:.2f} GB"
            ]
            
            if not found_client.get('is_wired'):
                output.append(f"Signal: {found_client.get('signal', 'N/A')} dBm")
            
            return "\n".join(output)
        
        elif query_type == "top_bandwidth":
            # Get top bandwidth users
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/sta"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            clients = response.json().get('data', [])
            
            # Calculate total bandwidth and sort
            bandwidth_clients = []
            for client in clients:
                rx = client.get('rx_bytes', 0)
                tx = client.get('tx_bytes', 0)
                total = rx + tx
                if total > 0:
                    bandwidth_clients.append({
                        'hostname': client.get('hostname', 'Unknown'),
                        'ip': client.get('last_ip', 'N/A'),
                        'rx': rx,
                        'tx': tx,
                        'total': total
                    })
            
            bandwidth_clients.sort(key=lambda x: x['total'], reverse=True)
            
            output = ["Top Bandwidth Users:"]
            for i, client in enumerate(bandwidth_clients[:10], 1):
                rx_gb = client['rx'] / 1e9
                tx_gb = client['tx'] / 1e9
                output.append(f"{i}. {client['hostname']} ({client['ip']}): RX {rx_gb:.2f} GB, TX {tx_gb:.2f} GB")
            
            return "\n".join(output)
        
        elif query_type == "recent_alerts":
            # Get recent alerts (last 24h)
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/alarm"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            alerts = response.json().get('data', [])
            
            # Filter last 24h
            from datetime import datetime, timedelta
            day_ago = (datetime.now() - timedelta(days=1)).timestamp() * 1000
            recent = [a for a in alerts if a.get('time', 0) > day_ago]
            
            if not recent:
                return "No alerts in the last 24 hours"
            
            output = [f"Recent Alerts ({len(recent)} in last 24h):"]
            for i, alert in enumerate(recent[:10], 1):
                time_ms = alert.get('time', 0)
                time_str = datetime.fromtimestamp(time_ms/1000).strftime('%H:%M')
                msg = alert.get('msg', 'Unknown alert')
                output.append(f"{i}. [{time_str}] {msg[:100]}")
            
            if len(recent) > 10:
                output.append(f"... and {len(recent) - 10} more")
            
            return "\n".join(output)
        
        elif query_type == "device_status":
            # Get all device statuses
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/device"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            devices = response.json().get('data', [])
            
            output = [f"UniFi Devices ({len(devices)} total):"]
            for device in devices:
                name = device.get('name', 'Unknown')
                state = device.get('state', 0)
                status = 'Online' if state == 1 else 'Offline'
                model = device.get('model', 'N/A')
                version = device.get('version', 'N/A')
                uptime = device.get('uptime', 0)
                uptime_hours = uptime // 3600
                output.append(f"- {name} ({model}): {status}, v{version}, Uptime: {uptime_hours}h")
            
            return "\n".join(output)
        
        elif query_type == "system_health":
            # Get overall system health
            url = f"{base_url}/proxy/network/api/s/{site_id}/stat/health"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            health = response.json().get('data', [])
            
            output = ["System Health:"]
            for subsystem in health:
                name = subsystem.get('subsystem', 'unknown').upper()
                status = subsystem.get('status', 'unknown').upper()
                output.append(f"- {name}: {status}")
                
                # Add extra details
                if name == 'WAN':
                    wan_ip = subsystem.get('wan_ip', 'N/A')
                    output[-1] += f" (IP: {wan_ip})"
                elif name == 'WLAN':
                    users = subsystem.get('num_user', 0)
                    output[-1] += f" ({users} clients)"
            
            return "\n".join(output)
        
        elif query_type == "port_forwards":
            # List port forwarding rules
            url = f"{base_url}/proxy/network/api/s/{site_id}/rest/portforward"
            response = session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            forwards = response.json().get('data', [])
            
            if not forwards:
                return "No port forwarding rules configured"
            
            output = [f"Port Forwarding Rules ({len(forwards)} total):"]
            for rule in forwards:
                name = rule.get('name', 'Unnamed')
                enabled = rule.get('enabled', False)
                proto = rule.get('proto', 'tcp').upper()
                dst_port = rule.get('dst_port', 'N/A')
                fwd_port = rule.get('fwd_port', 'N/A')
                status = 'Enabled' if enabled else 'Disabled'
                output.append(f"- {name}: {proto}/{dst_port} -> {fwd_port} ({status})")
            
            return "\n".join(output)
        
        else:
            return f"Unknown query type: {query_type}. Supported: dhcp_leases, dhcp_stats, next_ip, clients_active, clients_count, clients_bandwidth, network_info, firewall_rules, port_forwarding, device_info"
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "UniFi authentication failed. Check your API token or credentials in add-on configuration."
        return f"UniFi API error: {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        logger.error(f"UniFi Controller query error: {e}", exc_info=True)
        return f"UniFi query failed: {e}"


# ===== CAMERA ANALYSIS (GEMINI VISION) =====

def analyze_camera(camera_entity: str, question: str = "What do you see in this image?"):
    """
    Analyze a camera snapshot using Gemini Vision.
    Grabs a snapshot from a Home Assistant camera entity and sends it to Gemini for analysis.
    
    Args:
        camera_entity: Entity ID of the camera (e.g., "camera.garden", "camera.front_door")
        question: What to ask about the image (e.g., "What's in the garden?", "Is anyone at the door?")
    """
    import base64
    
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: Home Assistant connection not configured."
    
    # Check if either Vertex AI or AI Studio is configured
    if not config.GCP_PROJECT_ID and not config.GEMINI_API_KEY:
        return "Error: Neither Vertex AI (GCP Project) nor AI Studio (API key) is configured for vision analysis."
    
    try:
        # Step 1: Get camera snapshot from Home Assistant
        # Normalize entity ID
        if not camera_entity.startswith("camera."):
            camera_entity = f"camera.{camera_entity}"
        
        snapshot_url = f"{config.HA_URL}/api/camera_proxy/{camera_entity}"
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
        }
        
        logger.info(f"Fetching camera snapshot from {camera_entity}")
        snapshot_response = requests.get(snapshot_url, headers=headers, timeout=10)
        
        if snapshot_response.status_code == 404:
            return f"Camera '{camera_entity}' not found. Use search_ha_entities to find available cameras."
        
        snapshot_response.raise_for_status()
        
        image_data = snapshot_response.content
        
        # Step 2: Send to Gemini Vision
        # Use Vertex AI if configured, otherwise use AI Studio
        if config.GCP_PROJECT_ID:
            # Vertex AI mode
            import vertexai
            from vertexai.generative_models import GenerativeModel, Part
            import os
            
            # Initialize Vertex AI
            credentials_path = "/data/gcp-credentials.json"
            if os.path.exists(credentials_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            
            # Use configured location
            vertexai.init(project=config.GCP_PROJECT_ID, location=config.GCP_LOCATION)
            
            # Use user-configured model
            model = GenerativeModel(config.GEMINI_MODEL)
            
            # Create image part
            image_part = Part.from_data(image_data, mime_type="image/jpeg")
            
            logger.debug(f"Sending image to Vertex AI Vision ({config.GCP_LOCATION}) for analysis")
            response = model.generate_content([question, image_part])
            
            # Clean response text (remove bullet points etc if model ignores system prompt)
            analysis = response.text.replace("*", "").replace("- ", "").strip()
            return f"Camera analysis for {camera_entity}:\n{analysis}"
        
        else:
            # AI Studio mode (original implementation)
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            content_type = snapshot_response.headers.get('Content-Type', 'image/jpeg')
            
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
            
            vision_payload = {
                "contents": [{
                    "parts": [
                        {"text": question},
                        {
                            "inline_data": {
                                "mime_type": content_type,
                                "data": image_base64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 512
                }
            }
            
            
            logger.info(f"Sending image to AI Studio Gemini Vision for analysis")
            vision_response = requests.post(gemini_url, json=vision_payload, timeout=30)
            vision_response.raise_for_status()
            
            result = vision_response.json()
            
            # Extract the text response
            if 'candidates' in result and result['candidates']:
                text_parts = result['candidates'][0].get('content', {}).get('parts', [])
                if text_parts:
                    analysis = text_parts[0].get('text', 'No analysis available.')
                    return f"Camera analysis for {camera_entity}:\n{analysis}"
            
            return "Could not get analysis from Gemini Vision."
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Camera '{camera_entity}' not found."
        return f"Camera analysis error: {e}"
    except Exception as e:
        logger.error(f"Camera analysis error: {e}", exc_info=True)
        return f"Camera analysis error: {e}"


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
        origin: Starting location (address or place name, or 'home' to use saved location)
        destination: Destination (address or place name)
        mode: Travel mode - "driving", "walking", "bicycling", "transit"
    """
    if not config.GOOGLE_MAPS_API_KEY:
        return "Error: Google Maps API key not configured. Add google_maps_api_key to add-on configuration."
    
    # Resolve 'home' to saved location
    from memory import Memory
    memory = Memory()
    
    # Helper function to resolve location names
    def resolve_location(location: str) -> str:
        """Check if location is a saved preference and resolve it to actual address."""
        # First try exact match with common location prefixes
        for prefix in ["", "location_", "address_"]:
            saved = memory.get_preference(f"{prefix}{location.lower()}")
            if saved:
                logger.info(f"Resolved '{location}' to saved location: {saved}")
                return saved
        
        # Try checking if it's stored as "[name]_location" 
        saved = memory.get_preference(f"{location.lower()}_location")
        if saved:
            logger.info(f"Resolved '{location}' to saved location: {saved}")
            return saved
            
        # Return original if no match found
        return location
    
    # Resolve origin and destination
    origin = resolve_location(origin)
    destination = resolve_location(destination)
    
    # Check if we still have unresolved common location keywords
    if origin.lower() == "home":
        return "I don't have your home location saved yet, Sir. Please tell me where you live first, or provide a specific starting address."
    
    if destination.lower() == "home":
        return "I don't have your home location saved yet, Sir."
    
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


def _get_calendar_service():
    """Helper to get authenticated Google Calendar service."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        
        # Use same service account as Vertex AI
        credentials_path = os.path.join(os.path.dirname(__file__), ".cache", "google_credentials.json")
        
        if not os.path.exists(credentials_path):
            return None,  "Google service account credentials not found. Check GCP configuration."
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES)
        
        service = build('calendar', 'v3', credentials=credentials)
        return service, None
        
    except Exception as e:
        logger.error(f"Calendar service error: {e}", exc_info=True)
        return None, f"Failed to authenticate with Google Calendar: {e}"


def add_calendar_event(title: str, date_time: str, duration_minutes: int = 60, description: str = ""):
    """
    Add an event to Google Calendar.
    
    Args:
        title: Event title/summary
        date_time: Natural language or ISO format (e.g., "tomorrow at 2pm", "2024-12-25 14:00")
        duration_minutes: Event duration in minutes (default: 60)
        description: Optional event description
    
    Returns:
        Confirmation message with event details
    """
    if not config.GOOGLE_CALENDAR_ID:
        return "Error: Google Calendar ID not configured. Add google_calendar_id to add-on configuration."
    
    service, error = _get_calendar_service()
    if error:
        return f"Error: {error}"
    
    try:
        from datetime import datetime, timedelta
        import dateparser
        
        # Parse date/time
        parsed_dt = dateparser.parse(date_time, settings={'PREFER_DATES_FROM': 'future'})
        if not parsed_dt:
            return f"Could not parse date/time: '{date_time}'. Try formats like 'tomorrow at 2pm' or '2024-12-25 14:00'"
        
        # Create event
        start_time = parsed_dt.isoformat()
        end_time = (parsed_dt + timedelta(minutes=duration_minutes)).isoformat()
        
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Europe/London',  # Adjust to your timezone
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Europe/London',
            },
        }
        
        created_event = service.events().insert(calendarId=config.GOOGLE_CALENDAR_ID, body=event).execute()
        
        logger.info(f"Created calendar event: {title} at {parsed_dt}")
        return f"Added '{title}' to calendar on {parsed_dt.strftime('%A, %B %d at %I:%M %p')}"
        
    except Exception as e:
        logger.error(f"Calendar event creation error: {e}", exc_info=True)
        return f"Failed to create event: {e}"


def list_calendar_events(days_ahead: int = 7):
    """
    List upcoming calendar events.
    
    Args:
        days_ahead: Number of days to look ahead (default: 7)
    
    Returns:
        Formatted list of upcoming events
    """
    if not config.GOOGLE_CALENDAR_ID:
        return "Error: Google Calendar ID not configured. Add google_calendar_id to add-on configuration."
    
    service, error = _get_calendar_service()
    if error:
        return f"Error: {error}"
    
    try:
        from datetime import datetime, timedelta
        
        # Get events from now to days_ahead
        now = datetime.utcnow().isoformat() + 'Z'
        end_date = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=config.GOOGLE_CALENDAR_ID,
            timeMin=now,
            timeMax=end_date,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No upcoming events in the next {days_ahead} days"
        
        output = [f"Upcoming events ({len(events)}):"]
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No title')
            
            # Parse and format time
            try:
                if 'T' in start:  # DateTime
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_str = dt.strftime('%a, %b %d at %I:%M %p')
                else:  # All-day event
                    dt = datetime.fromisoformat(start)
                    time_str = dt.strftime('%a, %b %d (all day)')
                
                output.append(f"- {summary}: {time_str}")
            except:
                output.append(f"- {summary}: {start}")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Calendar list error: {e}", exc_info=True)
        return f"Failed to list events: {e}"


def create_location_reminder(message: str, location: str = "home", person_entity: str = "person.user"):
    """
    Create a location-based reminder using Home Assistant automation.
    The automation triggers once when the person arrives at the location, then deletes itself.
    
    Args:
        message: Reminder message
        location: Target location state (default: "home")
        person_entity: Person entity to track (default: "person.user")
    
    Returns:
        Confirmation message
    """
    if not config.HA_URL or not config.HA_TOKEN:
        return "Error: Home Assistant connection not configured"
    
    try:
        import uuid
        import requests
        
        # Generate unique automation ID
        automation_id = f"reminder_{uuid.uuid4().hex[:8]}"
        
        # Get the person entity to find their device tracker
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Query person entity state to get device_trackers
        person_url = f"{config.HA_URL}/api/states/{person_entity}"
        person_response = requests.get(person_url, headers=headers, timeout=10)
        person_data = person_response.json()
        
        # Find mobile app device tracker from person's attributes
        device_trackers = person_data.get('attributes', {}).get('source', [])
        if isinstance(device_trackers, str):
            device_trackers = [device_trackers]
        
        # Find mobile_app tracker
        mobile_device = None
        for tracker in device_trackers:
            if 'mobile_app' in tracker or 'device_tracker' in tracker:
                # Extract device name from tracker (e.g., device_tracker.pixel_7_pro -> pixel_7_pro)
                device_name = tracker.split('.')[-1]
                mobile_device = device_name
                break
        
        # Fallback to person name if no mobile device found
        if not mobile_device:
            person_name = person_entity.split('.')[-1]
            mobile_device = person_name
        
        mobile_notify_service = f"mobile_app_{mobile_device}"
        logger.info(f"Location reminder: Using notify service {mobile_notify_service} for {person_entity}")
        
        # Create automation config
        automation_config = {
            "id": automation_id,
            "alias": f"Reminder: {message[:50]}",
            "description": f"One-time location reminder created by Jarvis",
            "trigger": [
                {
                    "platform": "state",
                    "entity_id": person_entity,
                    "to": location
                }
            ],
            "action": [
                {
                    "service": f"notify.{mobile_notify_service}",
                    "data": {
                        "title": "📍 Location Reminder",
                        "message": message,
                        "data": {
                            "importance": "high",
                            "priority": "high",
                            "notification_icon": "mdi:bell-ring"
                        }
                    }
                },
                {
                    "service": "tts.speak",
                    "target": {
                        "entity_id": "tts.piper"
                    },
                    "data": {
                        "message": f"Reminder: {message}",
                        "media_player_entity_id": "media_player.everywhere"  # Adjust to your media player
                    }
                },
                {
                    "delay": "00:00:05"
                },
                {
                    "service": "automation.turn_off",
                    "target": {
                        "entity_id": f"automation.{automation_id}"
                    }
                },
                {
                    "service": "automation.delete",
                    "data": {
                        "entity_id": f"automation.{automation_id}"
                    }
                }
            ],
            "mode": "single"
        }
        
        # Create automation via HA API
        headers = {
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Use automations.yaml endpoint
        url = f"{config.HA_URL}/api/services/automation/reload"
        
        # First, we need to add to automations.yaml via file write service
        # But HA API doesn't allow direct automation creation, so we'll use the config API
        
        # Alternative: Use script service to create a one-shot script instead
        script_id = f"reminder_{uuid.uuid4().hex[:8]}"
        
        # Actually, let's use input_boolean as a flag and a separate automation
        # Best approach: Use the automation.trigger service with a helper
        
        # Simpler: Just create a persistent notification that checks location
        # But we want it to trigger automatically...
        
        # BEST: Use HA's built-in reminder integration if available, or create via automation API
        # Since we can't directly create automations via API easily, let's use a helper approach:
        
        # Create via the /api/config/automation/config/{id} endpoint
        automation_url = f"{config.HA_URL}/api/config/automation/config/{automation_id}"
        
        response = requests.post(automation_url, headers=headers, json=automation_config, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Created location reminder automation: {automation_id}")
        return f"I'll remind you to '{message}' when you arrive {location}"
        
    except Exception as e:
        logger.error(f"Location reminder error: {e}", exc_info=True)
        
        # Fallback: Create a simpler notification-based reminder
        try:
            # Just create a persistent notification as fallback
            url = f"{config.HA_URL}/api/services/persistent_notification/create"
            headers = {
                "Authorization": f"Bearer {config.HA_TOKEN}",
                "Content-Type": "application/json"
            }
            data = {
                "title": "Reminder Pending",
                "message": f"Remind: {message} (when you get {location})",
                "notification_id": f"reminder_{uuid.uuid4().hex[:8]}"
            }
            
            requests.post(url, headers=headers, json=data, timeout=10)
            return f"Created reminder: '{message}' (manual notification - automatic trigger unavailable)"
            
        except:
            return f"Failed to create location reminder: {e}"


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
        name: The preference name/key (e.g., "favorite_color", "phone_number", "spouse_name")
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

def delete_preference(name: str):
    """
    Delete a saved preference from memory.
    Use when user wants to forget or remove a saved preference.
    
    Args:
        name: The preference name/key to delete
        
    Returns:
        Confirmation message
    """
    try:
        memory = _get_memory()
        
        # Check if preference exists with exact match first
        value = memory.get_preference(name)
        if value is not None:
            key_to_delete = name
        else:
            # Try fuzzy match - find keys containing the search term
            all_prefs = memory.get_all_preferences()
            matches = [k for k in all_prefs.keys() if name.lower() in k.lower() or k.lower() in name.lower()]
            
            if not matches:
                return f"No preference found matching '{name}'. Use 'list all preferences' to see exact names."
            elif len(matches) == 1:
                key_to_delete = matches[0]
                logger.info(f"Fuzzy matched '{name}' to '{key_to_delete}'")
            else:
                # Multiple matches
                match_list = '\n'.join(f"  - {k}" for k in matches)
                return f"Multiple preferences match '{name}':\n{match_list}\n\nPlease be more specific."
        
        # Delete from database
        cursor = memory.conn.cursor()
        cursor.execute("DELETE FROM preferences WHERE key = ?", (key_to_delete,))
        memory.conn.commit()
        
        logger.info(f"Deleted preference: {key_to_delete}")
        return f"Successfully deleted preference: {key_to_delete}"
    except Exception as e:
        logger.error(f"Error deleting preference: {e}", exc_info=True)
        return f"Failed to delete preference: {e}"

def get_current_time():
    """
    Get the current date and time.
    Use this when the user asks about the current date, time, or needs calculations involving dates.
    
    Returns:
        Current date and time with timezone
    """
    from datetime import datetime, timezone
    
    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)
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
