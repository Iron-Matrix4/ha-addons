# ArchiSteamFarm (ASF) - Steam Free Games Claimer

Standalone Home Assistant addon for automatically claiming free Steam games using ArchiSteamFarm.

## Features

- ✅ Automatically claims free Steam games
- ✅ Configurable review score filtering (1-9 scale)
- ✅ Filter by game age (MaxDaysOld)
- ✅ Ignore free weekends option
- ✅ **Badge farming (automatic Steam trading card drops)**
- ✅ Headless operation (no manual interaction needed)
- ✅ Web UI accessible on port 1242

## Configuration

### Required Settings

- **steam_username**: Your Steam account username
- **steam_password**: Your Steam account password

### Free Game Claiming Filters

- **min_review_score** (default: 7 = Positive)
  - 1 = Overwhelmingly Negative
  - 4 = Mixed
  - 6 = Mostly Positive (70-79%)
  - **7 = Positive (80-100%)** ← Recommended
  - 8 = Very Positive (80-94%)
  - 9 = Overwhelmingly Positive (95-100%)
  - **0 = Claim all free games (no review filter)**

- **ignore_free_weekends** (default: true)
  - Skip games that are only free for the weekend

- **max_days_old** (default: 1095 = 3 years)
  - Only claim games released within this many days
  - **Set to 0 for no age limit** (claim all ages)

### Badge Farming Settings

- **enable_badge_farming** (default: true)
  - Enable automatic Steam trading card farming

- **farming_order** (default: 3)
  - 0 = Unordered (random)
  - 1 = By AppID (numerical order)
  - 2 = By name (alphabetical)
  - **3 = By playtime remaining (fastest first)** ← Recommended
  - 4 = By badge levels
  - 5 = By release date
  - Plus more - see [ASF Wiki](https://github.com/JustArchiNET/ArchiSteamFarm/wiki/Configuration#farmingorders)

- **idle_refundable_games** (default: false)
  - If true, will farm games within Steam's 2-hour refund window
  - **False recommended** for safety (prevents affecting refund eligibility)

- **notify_on_farming_finished** (default: true)
  - Send notification when all card drops are complete

## First-Time Setup

1. Install the addon
2. Configure your Steam credentials
3. Configure filtering and farming settings
4. Start the addon
5. **First login requires 2FA approval**:
   - Check your Steam Mobile Authenticator app
   - Approve the login request
   - OR enter the code when prompted in logs

After first successful login, ASF will remember your device and auto-login in the future.

### Skip 2FA (Advanced)

If you already run ASF on another machine, you can copy the authentication files:

```bash
# Copy from Windows ASF to Home Assistant
scp "C:\ASF\config\*.db" root@ha-ip:/config/asf/config/
scp "C:\ASF\config\*.maFile" root@ha-ip:/config/asf/config/
```

This allows instant login without Steam Guard prompts.

## Web Interface

Access the ASF IPC web interface at:

```
http://your-ha-ip:1242
```

## How It Works

### Free Game Claiming

ASF continuously monitors Steam for free packages (100% off sales) that match your filters:

- Must be temporarily free (not always-free games)
- Not demos, playtests, or free weekends
- Meets review score requirements
- Released within age limit

When found, ASF automatically adds them to your account.

### Badge Farming

ASF scans your Steam library for games with remaining trading card drops:

1. Identifies games with cards left to drop
2. "Idles" these games (runs them in background)
3. Drops cards automatically
4. Moves to next game when complete

## Troubleshooting

### "MinReviewScore: 0" in logs despite setting it to 7

This is expected! The logs show ASF's default values, but your configuration IS being applied. Check claimed games to verify filtering works.

### Bot stops after "RequestInput() input is invalid!"

You need to complete 2FA authentication. Check logs for the 2FA prompt and approve via Steam Mobile Authenticator.

### No games being claimed

1. Check `min_review_score` - try lowering it to 0 (claim all)
2. Set `max_days_old` to 0 (no age limit)
3. Set `ignore_free_weekends` to false
4. Check ASF logs for filter details
5. **There may simply be no free games available right now**

### Badge farming says "Nothing to farm"

1. Ensure `enable_badge_farming` is set to `true`
2. Check that you own games with card drops remaining
3. View the ASF web UI at port 1242 to see farming status

## Important Notes

⚠️ **Security**: This addon stores your Steam credentials in plain text in Home Assistant config. Ensure your HA instance is secure.

⚠️ **Review Score Filter**: Setting `min_review_score` too high may prevent claiming most free games. Start with 0 or 1 to test.

⚠️ **Refundable Games**: Keep `idle_refundable_games` as `false` to avoid affecting refund eligibility.

## Support

For ASF-specific issues, see: <https://github.com/JustArchiNET/ArchiSteamFarm>
