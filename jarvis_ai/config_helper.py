"""
Configuration helper for Jarvis Add-on.
Loads configuration from environment variables set by Home Assistant.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Debug logging
logger.info(f"Loading config from environment...")
logger.info(f"GEMINI_API_KEY present: {bool(os.getenv('GEMINI_API_KEY'))}")

# ===== API KEYS =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "europe-west1")  # Default Vertex AI location
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ===== HOME ASSISTANT =====
# These are auto-provided by HA to add-ons
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
HA_TOKEN = os.getenv("SUPERVISOR_TOKEN", "")

# ===== SPOTIFY =====
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID", "")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "")

# ===== RADARR =====
RADARR_URL = os.getenv("RADARR_URL", "")
RADARR_API_KEY = os.getenv("RADARR_API_KEY", "")

# ===== SONARR =====
SONARR_URL = os.getenv("SONARR_URL", "")
SONARR_API_KEY = os.getenv("SONARR_API_KEY", "")

# ===== GOOGLE CUSTOM SEARCH =====
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")

# ===== GOOGLE MAPS =====
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ===== GOOGLE CALENDAR =====
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")

# ===== QBITTORRENT =====
QBITTORRENT_URL = os.getenv("QBITTORRENT_URL", "")
QBITTORRENT_USERNAME = os.getenv("QBITTORRENT_USERNAME", "")
QBITTORRENT_PASSWORD = os.getenv("QBITTORRENT_PASSWORD", "")

# ===== PROWLARR =====
PROWLARR_URL = os.getenv("PROWLARR_URL", "")
PROWLARR_API_KEY = os.getenv("PROWLARR_API_KEY", "")

# ===== UNIFI CONTROLLER (ADVANCED) =====
UNIFI_CONTROLLER_URL = os.getenv("UNIFI_CONTROLLER_URL", "")
UNIFI_CONTROLLER_API_TOKEN = os.getenv("UNIFI_CONTROLLER_API_TOKEN", "")
UNIFI_CONTROLLER_USERNAME = os.getenv("UNIFI_CONTROLLER_USERNAME", "")
UNIFI_CONTROLLER_PASSWORD = os.getenv("UNIFI_CONTROLLER_PASSWORD", "")
UNIFI_SITE_ID = os.getenv("UNIFI_SITE_ID", "default")

# ===== UNIFI (for VPN check) =====
UNIFI_WAN_SENSOR = os.getenv("UNIFI_WAN_SENSOR", "sensor.unifi_gateway_wan_ip")

# ===== LLM CONFIGURATION =====
LLM_PROVIDER = "gemini"  # Always use Gemini for now
