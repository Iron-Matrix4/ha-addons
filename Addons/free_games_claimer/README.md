# Free Games Claimer with Steam Support

Automatically claims free games from **Epic Games Store**, **Amazon Prime Gaming**, **GOG**, and **Steam**.

This is an enhanced fork of [alexbelgium/hassio-addons/free_games_claimer](https://github.com/alexbelgium/hassio-addons/tree/master/free_games_claimer) with added **Steam support** via ArchiSteamFarm.

## Features

- 🎮 **Epic Games Store** - Automatic weekly free game claiming
- 🎁 **Amazon Prime Gaming** - Monthly free games and in-game loot
- 🕹️ **GOG** - Periodic free game offers
- ⚙️ **Steam** - Automatic free package discovery and claiming via ArchiSteamFarm
  - Discovers packages via Steam PICS system
  - Monitors gaming subreddits for popular releases
  - Supports advanced filtering (trading cards, time-limited, DLC, etc.)
- 🔔 Notification support (Apprise compatible)
- 🖥️ NoVNC web interface for troubleshooting
- 🏠 Full Home Assistant integration

## Installation

1. Add this repository to your Home Assistant Supervisor:
   - Open **Supervisor** → **Add-on Store** → **⋮** (three dots) → **Repositories**
   - Add: `https://github.com/YOUR_USERNAME/hassio-addons` (update after you fork/publish)

2. Install the **Free Games Claimer** add-on
3. Configure the add-on (see Configuration section below)
4. Start the add-on

## Configuration

### Basic Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CMD_ARGUMENTS` | string | `node epic-games ; node prime-gaming ; node gog` | Commands to run for Epic/Prime/GOG |
| `CONFIG_LOCATION` | string | `/config/config.env` | Location of vogler claimer config file |
| `ENABLE_STEAM` | boolean | `false` | Enable/disable Steam claiming via ASF |
| `ASF_BOT_NAME` | string | `SteamBot` | Name for your Steam bot configuration |
| `env_vars` | list | `[]` | Additional environment variables |

### Epic Games / Prime Gaming / GOG Setup

1. After first start, a `config.env` file will be created in `/config/`
2. Edit this file to configure options from [vogler/free-games-claimer](https://github.com/vogler/free-games-claimer#configuration--options)
3. Key settings you may want to configure:

   ```bash
   # Notification settings
   NOTIFY_TITLE='Free Games Claimer'
   APPRISE_URL=discord://webhook_id/webhook_token  # For Discord notifications
   
   # Browser settings
   SHOW=1          # Set to 1 to see browser (via NoVNC), 0 for headless
   WIDTH=1280
   HEIGHT=1280
   TIMEOUT=60
   LOGIN_TIMEOUT=180
   ```

### Steam Setup (ArchiSteamFarm)

1. **Enable Steam in addon configuration:**
   - Set `ENABLE_STEAM: true`
   - Optionally customize `ASF_BOT_NAME` (default: `SteamBot`)

2. **Configure Steam credentials:**
   After the first run, two config files will be created in `/config/asf/config/`:

   - **ASF.json** - Global ASF settings (usually no changes needed)
   - **SteamBot.json** (or your custom bot name) - Bot-specific config

   Edit `SteamBot.json` and update Steam credentials:

   ```json
   {
     "Enabled": true,
     "SteamLogin": "your_steam_username",
     "SteamPassword": "your_steam_password",
     "EnableFreePackages": true,
     "PauseFreePackagesWhilePlaying": true,
     "FreePackagesFilters": [
       { "NoCostOnly": true },
       { "Categories": [29] },
       { "Types": ["DLC"], "IgnoredTypes": ["Game", "Application"] }
     ]
   }
   ```

3. **Steam Guard / 2FA:**
   - On first login, ASF will prompt for your Steam Guard code
   - Check addon logs and enter the code when prompted
   - ASF will remember your device after successful authentication

### Steam Package Filtering

The default configuration claims:

- ✅ Limited-time free games (NoCostOnly)
- ✅ Games with trading cards (Category 29)
- ✅ Free DLC for games you own

**To claim everything** (games, DLC, demos, playtests):

```json
"FreePackagesFilters": [
  {
    "IgnoredTypes": [],
    "PlaytestMode": 3
  }
]
```

**To claim only full games** (no demos/playtests):

```json
"FreePackagesFilters": [
  {
    "NoCostOnly": true,
    "IgnoredTypes": ["Demo", "Playtest"]
  }
]
```

**To claim only games with trading cards:**

```json
"FreePackagesFilters": [
  {
    "Categories": [29]
  }
]
```

See [FreePackages documentation](https://github.com/Citrinate/FreePackages#enabling-package-filters) for more filter options.

## Usage

### Automatic Operation

- The addon runs the configured commands on startup
- For continuous claiming, set up a Home Assistant automation to restart the addon periodically (e.g., daily)

### Manual Operation

- Access the NoVNC interface at `http://homeassistant.local:6080` (or your HA IP)
- Watch the browser automation in action
- Useful for debugging login issues

### Checking Logs

- View addon logs in Home Assistant Supervisor
- Epic/Prime/GOG logs show claimed games
- ASF logs show Steam package activations

## Notifications

### For Epic/Prime/GOG (via Apprise)

Configure notification URLs in `/config/config.env`:

```bash
# Discord
APPRISE_URL=discord://webhook_id/webhook_token

# Telegram
APPRISE_URL=tgram://bot_token/chat_id

# Email
APPRISE_URL=mailto://user:password@gmail.com

# Multiple services (comma-separated)
APPRISE_URL=discord://...,tgram://...
```

See [Apprise documentation](https://github.com/caronc/apprise) for all supported services.

### For Steam (ASF Notifications)

ASF can send notifications through its own system. Edit `ASF.json`:

```json
{
  "SteamOwnerID": 76561198XXXXXXXXX
}
```

Set your Steam64 ID to receive Steam chat notifications from ASF.

## Troubleshooting

### Epic/Prime/GOG Issues

- **Login failures**: Enable `SHOW=1` in config.env and use NoVNC to see what's happening
- **2FA prompts**: Check addon logs for OTP requests
- **Captchas**: May require manual intervention via NoVNC

### Steam / ASF Issues

- **ASF won't start**: Check `/config/asf/config/SteamBot.json` for syntax errors
- **Invalid credentials**: Verify Steam username/password in bot config
- **Steam Guard code needed**: Check addon logs for Steam Guard prompts
- **No packages found**: ASF discovers packages gradually; check logs after 12-24 hours
- **Filters not working**: Validate JSON syntax in `FreePackagesFilters` array

### General

- Check addon logs for error messages
- Restart the addon after config changes
- Verify file permissions in `/config/` directory

## File Structure

```
/config/
├── config.env                    # vogler claimer config (Epic/Prime/GOG)
└── asf/
    └── config/
        ├── ASF.json              # ASF global configuration
        └── SteamBot.json         # Steam bot configuration
```

## Credits

- Original addon: [alexbelgium/hassio-addons](https://github.com/alexbelgium/hassio-addons)
- Epic/Prime/GOG claiming: [vogler/free-games-claimer](https://github.com/vogler/free-games-claimer)
- Steam claiming: [ArchiSteamFarm](https://github.com/JustArchiNET/ArchiSteamFarm)
- FreePackages plugin: [Citrinate/FreePackages](https://github.com/Citrinate/FreePackages)

## License

MIT License - see LICENSE file for details
