#!/bin/bash
set -e

CONFIG_PATH="/data/options.json"

echo "Starting ArchiSteamFarm addon..."

if [ ! -f "$CONFIG_PATH" ]; then
    echo "Config file not found at $CONFIG_PATH"
    exit 1
fi

# Get addon configuration using jq
STEAM_USER="$(jq -r '.steam_username // empty' $CONFIG_PATH)"
STEAM_PASS="$(jq -r '.steam_password // empty' $CONFIG_PATH)"
MIN_SCORE="$(jq -r '.min_review_score // 7' $CONFIG_PATH)"
IGNORE_WEEKENDS="$(jq -r '.ignore_free_weekends // true' $CONFIG_PATH)"
MAX_DAYS="$(jq -r '.max_days_old // 1095' $CONFIG_PATH)"
ENABLE_FARMING="$(jq -r '.enable_badge_farming // true' $CONFIG_PATH)"
FARMING_ORDER="$(jq -r '.farming_order // 3' $CONFIG_PATH)"
IDLE_REFUNDABLE="$(jq -r '.idle_refundable_games // false' $CONFIG_PATH)"
NOTIFY_FARMING="$(jq -r '.notify_on_farming_finished // true' $CONFIG_PATH)"

# Validate required fields
if [ -z "$STEAM_USER" ] || [ -z "$STEAM_PASS" ]; then
    echo "Error: Steam username and password are required!"
    exit 1
fi

echo "Generating ASF configuration..."
echo "Steam User: $STEAM_USER"
echo "MinReviewScore: $MIN_SCORE"

# Create ASF config directory
mkdir -p /config/asf/config

# Generate ASF.json (global config)
cat > /config/asf/ASF.json <<EOF
{
  "Headless": true,
  "IPC": true,
  "IPCHost": "0.0.0.0",
  "IPCPort": 1242,
  "SteamOwnerID": 0
}
EOF

# Generate SteamBot.json (bot config) with badge farming settings
# Calculate FarmingPreferences value (0 = disabled, 3 = all optimizations)
if [ "$ENABLE_FARMING" = "true" ]; then
  FARMING_PREFS=3
else
  FARMING_PREFS=0
fi

cat > /config/asf/config/SteamBot.json <<EOF
{
  "Enabled": true,
  "SteamLogin": "$STEAM_USER",
  "SteamPassword": "$STEAM_PASS",
  "Headless": true,
  "EnableFreePackages": true,
  "PauseFreePackagesWhilePlaying": true,
  "FreePackagesFilters": [
    {
      "NoCostOnly": true,
      "Types": ["Game", "DLC"],
      "IgnoredTypes": ["Demo", "Playtest", "Application", "Video", "Music"],
      "IgnoreFreeWeekends": $IGNORE_WEEKENDS,
      "MinReviewScore": $MIN_SCORE,
      "MinDaysOld": 0,
      "MaxDaysOld": $MAX_DAYS
    }
  ],
  "FarmingPreferences": $FARMING_PREFS,
  "FarmingOrders": [$FARMING_ORDER],
  "GamesPlayedWhileIdle": [],
  "IdleRefundableGames": $IDLE_REFUNDABLE,
  "IdlePriorityQueueOnly": false,
  "SendOnFarmingFinished": $NOTIFY_FARMING
}
EOF

echo "Generated SteamBot.json with MinReviewScore: $MIN_SCORE"
echo "Active FreePackagesFilters:"
jq '.FreePackagesFilters' /config/asf/config/SteamBot.json

# Database files are preserved to maintain login session
if [ -d "/config/asf" ]; then
    echo "Checking for existing config..."
fi

echo "Starting ASF..."
echo "ASF IPC web interface will be available on port 1242"

# Start auto-trigger script in background
/etc/cont-init.d/auto_trigger.sh &

# Start ASF with config directory
# Start ASF with config directory using dotnet, pipe output to monitor for notifications
cd /app/asf
dotnet ArchiSteamFarm.dll --path /config/asf | /etc/cont-init.d/monitor_claims.sh
