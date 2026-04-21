"""
Vertex AI function declarations for Jarvis tools using the modern google-genai SDK.
"""
from google.genai import types

# Function Declarations defined as dictionaries for the new SDK
control_home_assistant_func = {
    "name": "control_home_assistant",
    "description": "Control a Home Assistant entity (lights, switches, climate devices, etc.)",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "entity_id": {
                "type": "STRING",
                "description": "The ID of the entity (e.g., 'light.office', 'climate.bedroom')"
            },
            "command": {
                "type": "STRING",
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
                "type": "STRING",
                "description": "Optional parameter: temperature value, hvac_mode, etc."
            }
        },
        "required": ["entity_id", "command"]
    }
}

get_ha_state_func = {
    "name": "get_ha_state",
    "description": "Get the current state of a Home Assistant entity",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "entity_id": {"type": "STRING", "description": "The ID of the entity"}
        },
        "required": ["entity_id"]
    }
}

search_ha_entities_func = {
    "name": "search_ha_entities",
    "description": "Search for Home Assistant entities by name",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Search query"}
        },
        "required": ["query"]
    }
}

get_person_location_func = {
    "name": "get_person_location",
    "description": "Get the current location of a person",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "person_name": {"type": "STRING", "description": "Name of the person"}
        },
        "required": ["person_name"]
    }
}

get_appliance_status_func = {
    "name": "get_appliance_status",
    "description": "Get intelligent status of an appliance",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "appliance_name": {"type": "STRING", "description": "Name of the appliance"}
        },
        "required": ["appliance_name"]
    }
}

get_weather_func = {
    "name": "get_weather",
    "description": "Get comprehensive weather",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "city": {"type": "STRING", "description": "City name"},
            "forecast_hours": {"type": "INTEGER", "description": "Hours to forecast"}
        }
    }
}

get_travel_time_func = {
    "name": "get_travel_time",
    "description": "Get real-time travel time",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "origin": {"type": "STRING", "description": "Starting location"},
            "destination": {"type": "STRING", "description": "Destination"},
            "mode": {"type": "STRING", "enum": ["driving", "walking", "bicycling", "transit"]}
        },
        "required": ["origin", "destination"]
    }
}

google_search_func = {
    "name": "google_search",
    "description": "Search the web for general knowledge",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Search query"}
        },
        "required": ["query"]
    }
}

add_calendar_event_func = {
    "name": "add_calendar_event",
    "description": "Add an event to Google Calendar",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING"},
            "date_time": {"type": "STRING"},
            "duration_minutes": {"type": "INTEGER"}
        },
        "required": ["title", "date_time"]
    }
}

list_calendar_events_func = {
    "name": "list_calendar_events",
    "description": "List upcoming calendar events",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "days_ahead": {"type": "INTEGER"}
        }
    }
}

create_location_reminder_func = {
    "name": "create_location_reminder",
    "description": "Create a location-based reminder",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "message": {"type": "STRING"},
            "location": {"type": "STRING"}
        },
        "required": ["message"]
    }
}

play_music_func = {
    "name": "play_music",
    "description": "Play music on Spotify",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING"},
            "device": {"type": "STRING"}
        },
        "required": ["query"]
    }
}

save_preference_func = {
    "name": "save_preference",
    "description": "Save user preference",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "value": {"type": "STRING"}
        },
        "required": ["name", "value"]
    }
}

get_preference_func = {
    "name": "get_preference",
    "description": "Get user preference",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"}
        },
        "required": ["name"]
    }
}

delete_preference_func = {
    "name": "delete_preference",
    "description": "Delete user preference",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"}
        },
        "required": ["name"]
    }
}

get_current_time_func = {
    "name": "get_current_time",
    "description": "Get current time",
    "parameters": {"type": "OBJECT", "properties": {}}
}

query_radarr_func = {
    "name": "query_radarr",
    "description": "Query Radarr movie library",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query_type": {"type": "STRING", "enum": ["status", "stats", "last_downloaded", "recent", "search", "missing"]},
            "movie_name": {"type": "STRING"}
        },
        "required": ["query_type"]
    }
}

add_to_radarr_func = {
    "name": "add_to_radarr",
    "description": "Add movie to Radarr",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "movie_name": {"type": "STRING"}
        },
        "required": ["movie_name"]
    }
}

query_sonarr_func = {
    "name": "query_sonarr",
    "description": "Query Sonarr series library",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query_type": {"type": "STRING", "enum": ["status", "stats", "last_downloaded", "recent", "search", "missing"]},
            "series_name": {"type": "STRING"}
        },
        "required": ["query_type"]
    }
}

add_to_sonarr_func = {
    "name": "add_to_sonarr",
    "description": "Add series to Sonarr",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "series_name": {"type": "STRING"}
        },
        "required": ["series_name"]
    }
}

query_qbittorrent_func = {
    "name": "query_qbittorrent",
    "description": "Query qBittorrent status",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query_type": {"type": "STRING", "enum": ["status", "stats", "speed", "downloading", "completed"]}
        },
        "required": ["query_type"]
    }
}

query_prowlarr_func = {
    "name": "query_prowlarr",
    "description": "Query Prowlarr status",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query_type": {"type": "STRING", "enum": ["status", "stats", "indexers"]}
        },
        "required": ["query_type"]
    }
}

check_vpn_status_func = {
    "name": "check_vpn_status",
    "description": "Check VPN status",
    "parameters": {"type": "OBJECT", "properties": {}}
}

query_unifi_network_func = {
    "name": "query_unifi_network",
    "description": "Query UniFi network via Home Assistant",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query_type": {"type": "STRING", "enum": ["wan_ip", "devices", "bandwidth", "uptime", "stats"]}
        },
        "required": ["query_type"]
    }
}

query_unifi_controller_func = {
    "name": "query_unifi_controller",
    "description": "Query UniFi Controller API directly",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query_type": {"type": "STRING", "enum": ["dhcp_leases", "dhcp_stats", "next_ip", "network_stats", "clients_active", "clients_count", "wan_ip"]},
            "subnet": {"type": "STRING"},
            "client_id": {"type": "STRING"}
        },
        "required": ["query_type"]
    }
}

analyze_camera_func = {
    "name": "analyze_camera",
    "description": "Analyze camera snapshot using AI vision",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "camera_entity": {"type": "STRING"},
            "question": {"type": "STRING"}
        },
        "required": ["camera_entity"]
    }
}

# Create the Tool list for Modern Google GenAI SDK
jarvis_tool_list = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(**control_home_assistant_func),
            types.FunctionDeclaration(**get_ha_state_func),
            types.FunctionDeclaration(**search_ha_entities_func),
            types.FunctionDeclaration(**get_person_location_func),
            types.FunctionDeclaration(**get_appliance_status_func),
            types.FunctionDeclaration(**get_weather_func),
            types.FunctionDeclaration(**get_travel_time_func),
            types.FunctionDeclaration(**google_search_func),
            types.FunctionDeclaration(**add_calendar_event_func),
            types.FunctionDeclaration(**list_calendar_events_func),
            types.FunctionDeclaration(**create_location_reminder_func),
            types.FunctionDeclaration(**play_music_func),
            types.FunctionDeclaration(**save_preference_func),
            types.FunctionDeclaration(**get_preference_func),
            types.FunctionDeclaration(**delete_preference_func),
            types.FunctionDeclaration(**get_current_time_func),
            types.FunctionDeclaration(**query_radarr_func),
            types.FunctionDeclaration(**add_to_radarr_func),
            types.FunctionDeclaration(**query_sonarr_func),
            types.FunctionDeclaration(**add_to_sonarr_func),
            types.FunctionDeclaration(**query_qbittorrent_func),
            types.FunctionDeclaration(**query_prowlarr_func),
            types.FunctionDeclaration(**check_vpn_status_func),
            types.FunctionDeclaration(**query_unifi_network_func),
            types.FunctionDeclaration(**query_unifi_controller_func),
            types.FunctionDeclaration(**analyze_camera_func),
        ]
    )
]
