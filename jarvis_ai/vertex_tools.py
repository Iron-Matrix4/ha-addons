"""
Vertex AI function declarations for Jarvis tools.
Defines tools in the format required by Vertex AI Gemini.
"""
from vertexai.generative_models import FunctionDeclaration, Tool

# Home Assistant Control
control_home_assistant_func = FunctionDeclaration(
    name="control_home_assistant",
    description="Control a Home Assistant entity (lights, switches, climate devices, etc.)",
    parameters={
        "type": "object",
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "The ID of the entity (e.g., 'light.office', 'climate.bedroom')"
            },
            "command": {
                "type": "string",
                "description": "The action to perform",
                "enum": [
                    "turn_on", "turn_off", "toggle",
                    "set_temperature", "set_hvac_mode", "turn_up", "turn_down",
                    "close", "open", "stop", "set_cover_position",
                    "lock", "unlock",
                    "set_brightness", "set_color",
                    "play", "pause", "media_next", "media_previous", "volume_up", "volume_down"
                ]
            },
            "parameter": {
                "type": "string",
                "description": "Optional parameter: temperature value, hvac_mode (heat/cool/auto/off), cover position (0-100), brightness (0-100), color name or RGB (255,0,0)"
            }
        },
        "required": ["entity_id", "command"]
    }
)

get_ha_state_func = FunctionDeclaration(
    name="get_ha_state",
    description="Get the current state of a Home Assistant entity (temperature, light status, etc.)",
    parameters={
        "type": "object",
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "The ID of the entity to query (e.g., 'sensor.office_temperature')"
            }
        },
        "required": ["entity_id"]
    }
)

search_ha_entities_func = FunctionDeclaration(
    name="search_ha_entities",
    description="Search for Home Assistant entities by name when you don't know the exact entity_id",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (e.g., 'office light', 'bedroom temperature')"
            }
        },
        "required": ["query"]
    }
)

# Weather
get_weather_func = FunctionDeclaration(
    name="get_weather",
    description="Get comprehensive weather including current conditions, hourly forecast, and precipitation. Includes umbrella recommendations.",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name (default: 'London')"
            },
            "forecast_hours": {
                "type": "integer",
                "description": "Number of hours to forecast for precipitation (default: 12)"
            }
        },
        "required": []
    }
)

# Travel Time
get_travel_time_func = FunctionDeclaration(
    name="get_travel_time",
    description="Get real-time travel time between two locations with current traffic conditions using Google Maps",
    parameters={
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Starting location - address, place name, or 'home' to use saved home location"
            },
            "destination": {
                "type": "string",
                "description": "Destination - address or place name"
            },
            "mode": {
                "type": "string",
                "description": "Travel mode: 'driving', 'walking', 'bicycling', or 'transit'",
                "enum": ["driving", "walking", "bicycling", "transit"]
            }
        },
        "required": ["origin", "destination"]
    }
)

# Web Search
google_search_func = FunctionDeclaration(
    name="google_search",
    description="Search the web for general knowledge. Use this to answer questions you don't know.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            }
        },
        "required": ["query"]
    }
)

# Music
play_music_func = FunctionDeclaration(
    name="play_music",
    description="Play music on Spotify using Spotcast. Works on any media player device.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Song name, artist, or album to search for (e.g., 'Bohemian Rhapsody', 'Queen', 'Dark Side of the Moon')"
            },
            "device": {
                "type": "string",
                "description": "Device name to play on (e.g., 'Office Display', 'Living Room TV'). If not specified, will ask user to choose."
            },
            "entity_id": {
                "type": "string",
                "description": "Optional specific media_player entity_id (e.g., 'media_player.office_display'). Rarely needed."
            }
        },
        "required": ["query"]
    }
)

# Memory
save_preference_func = FunctionDeclaration(
    name="save_preference",
    description="Save user information to persistent memory. Use when user asks Jarvis to remember something (names, numbers, preferences, etc.). Does NOT save conversation context or errors.",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preference key name (e.g., 'wife_name', 'phone_number', 'favorite_color')"
            },
            "value": {
                "type": "string",
                "description": "Value to remember"
            }
        },
        "required": ["name", "value"]
    }
)

get_preference_func = FunctionDeclaration(
    name="get_preference",
    description="Retrieve saved user information from memory. Use when user asks what Jarvis remembers.",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preference key to retrieve"
            }
        },
        "required": ["name"]
    }
)

# Utility
get_current_time_func = FunctionDeclaration(
    name="get_current_time",
    description="Get current date and time. Use when user asks about the date, time, or needs date calculations (e.g., 'how many days until').",
    parameters={
        "type": "object",
        "properties": {}
    }
)

# Radarr Query
query_radarr_func = FunctionDeclaration(
    name="query_radarr",
    description="Query Radarr for movie library information and system status. Use for questions about movies, downloads, and Radarr status.",
    parameters={
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "description": "Type of query",
                "enum": ["status", "stats", "last_downloaded", "recent", "search", "missing"]
            },
            "movie_name": {
                "type": "string",
                "description": "Movie name (only needed for 'search' query)"
            }
        },
        "required": ["query_type"]
    }
)

add_to_radarr_func = FunctionDeclaration(
    name="add_to_radarr",
    description="Add a movie to Radarr by name. Will search and add the best match.",
    parameters={
        "type": "object",
        "properties": {
            "movie_name": {
                "type": "string",
                "description": "Name of the movie to add"
            }
        },
        "required": ["movie_name"]
    }
)

# Sonarr Query
query_sonarr_func = FunctionDeclaration(
    name="query_sonarr",
    description="Query Sonarr for TV series library information and system status. Use for questions about TV shows, episodes, downloads, and Sonarr status.",
    parameters={
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "description": "Type of query",
                "enum": ["status", "stats", "last_downloaded", "recent", "search", "missing"]
            },
            "series_name": {
                "type": "string",
                "description": "Series name (only needed for 'search' query)"
            }
        },
        "required": ["query_type"]
    }
)

add_to_sonarr_func = FunctionDeclaration(
    name="add_to_sonarr",
    description="Add a TV series to Sonarr by name. Will search and add the best match.",
    parameters={
        "type": "object",
        "properties": {
            "series_name": {
                "type": "string",
                "description": "Name of the TV series to add"
            }
        },
        "required": ["series_name"]
    }
)

# qBittorrent Query
query_qbittorrent_func = FunctionDeclaration(
    name="query_qbittorrent",
    description="Query qBittorrent for torrent download status and information. Use for questions about active downloads, speeds, and torrent status.",
    parameters={
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "description": "Type of query",
                "enum": ["status", "stats", "speed", "downloading", "completed"]
            }
        },
        "required": ["query_type"]
    }
)

# Prowlarr Query
query_prowlarr_func = FunctionDeclaration(
    name="query_prowlarr",
    description="Query Prowlarr for indexer status and information. Use for questions about search indexers.",
    parameters={
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "description": "Type of query",
                "enum": ["status", "stats", "indexers"]
            }
        },
        "required": ["query_type"]
    }
)

# VPN Status Check
check_vpn_status_func = FunctionDeclaration(
    name="check_vpn_status",
    description="Check if the VPN is connected on the download VM. Verifies qBittorrent connectivity and compares external IP to home WAN.",
    parameters={
        "type": "object",
        "properties": {}
    }
)

# Create the Tool object for Vertex AI
jarvis_tool = Tool(
    function_declarations=[
        control_home_assistant_func,
        get_ha_state_func,
        search_ha_entities_func,
        get_weather_func,
        get_travel_time_func,
        google_search_func,
        play_music_func,
        save_preference_func,
        get_preference_func,
        get_current_time_func,
        query_radarr_func,
        add_to_radarr_func,
        query_sonarr_func,
        add_to_sonarr_func,
        query_qbittorrent_func,
        query_prowlarr_func,
        check_vpn_status_func,
    ]
)
