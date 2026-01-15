#!/bin/bash
# auto_trigger.sh
# Waits for ASF to log in, then triggers farming via IPC

echo "[Auto-Trigger] Waiting for ASF to fully start..."
sleep 10

# Wait for ASF IPC to be ready
MAX_WAIT=30
COUNT=0
while [ $COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:1242/Api/ASF >/dev/null 2>&1; then
        echo "[Auto-Trigger] ASF IPC is ready!"
        break
    fi
    sleep 1
    COUNT=$((COUNT + 1))
done

if [ $COUNT -eq $MAX_WAIT ]; then
    echo "[Auto-Trigger] Timeout waiting for ASF IPC"
    exit 1
fi

# Wait a bit more for login to complete
sleep 5

echo "[Auto-Trigger] Sending start command to trigger farming..."
curl -X POST "http://localhost:1242/Api/Command" \
    -H "Content-Type: application/json" \
    -d '{"Command":"start SteamBot"}' 2>/dev/null

sleep 2

echo "[Auto-Trigger] Checking bot status..."
curl -X GET "http://localhost:1242/Api/Bot/SteamBot" 2>/dev/null | jq -r '.Result.CardsFarmer' 2>/dev/null || echo "Status check complete"

echo "[Auto-Trigger] ASF farming initialized!"
