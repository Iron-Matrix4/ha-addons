#!/bin/bash

# Wait for ASF to start
sleep 15

# Monitor the ASF process output (via the log file or pipe if we can tap it)
# Since we are inside the container, we can't easily tail the addon log itself from supervisor.
# Instead, we will wrap the execution in the start script to pipe output to this monitor.

while read -r line; do
    echo "$line"
    if [[ "$line" == *"Redeemed items"* ]]; then
        GAME_NAME=$(echo "$line" | sed 's/.*Redeemed items: //')
        
        # Send notification to Home Assistant
        curl -X POST \
             -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
             -H "Content-Type: application/json" \
             -d "{\"message\": \"ASF Claimed: $GAME_NAME\", \"title\": \"Free Game Claimed!\"}" \
             http://supervisor/core/api/services/notify/notify
    fi
done
