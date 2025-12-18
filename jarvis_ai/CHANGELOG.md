# Changelog

All notable changes to the Jarvis AI Home Assistant Add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## 1.1.3 (2025-12-18)

- **Latency Optimization (Phase 2)**: Condensed system prompt by 80% to reduce token overhead.
- **Improved Performance**: Pinning modern Google Cloud SDK versions for better connection stability and speed.
- **Context Window Tuning**: Reduced history window to 12 turns (6 exchanges) to maintain consistent response speeds over long sessions.

## 1.1.7 (2025-12-18)

- **Stability First**: Reverted all experimental system prompt and configuration changes to restore Jarvis's original intelligence and persona.
- **Smart Logic Restored**: Jarvis now once again understands room context and proactive tool searching (no more guessing wrong entities).
- **Latency Fixed**: Kept the London regional routing (`gcp_location`) for speed while returning to the stable "Smart" brain.

## 1.1.6 (2025-12-18)

- **Restored Persona**: Brought back the witty J.A.R.V.I.S. persona and Tony Stark references.
- **Dynamic Intelligence**: Fixed a bug where user preferences weren't actually being seen by the AI; they are now passed dynamically for every request.
- **Tool Chaining Fixes**: Jarvis will now strictly search for devices before guessing names and intelligently use `home_location` for weather.
- **Vision Stability**: Switched camera analysis to a more stable model and fixed regional routing to match the new `gcp_location` setting, resolving "Resource Exhausted" (429) errors.

## 1.1.5 (2025-12-18)

- **Bug Fix**: Fixed a crash in history management (`AttributeError: property 'history' of 'ChatSession' object has no setter`).
- **Improved Tooling**: Enhanced system instructions to ensure user preferences are correctly saved via the `save_preference` tool.

## 1.1.2 (2025-12-18)

- **Fix**: Added missing `save_preference` and `get_preference` tools to the Vertex AI schema, resolving "undeclared function" errors and safety blocks.
- **Improved Reliability**: Properly linked memory tools to the AI brain.

## 1.1.1 (2025-12-18)

- **Bug Fix**: Fixed a crash in history management (`AttributeError: property 'history' of 'ChatSession' object has no setter`).
- **Improved Tooling**: Enhanced system instructions to ensure user preferences are correctly saved via the `save_preference` tool.

## [1.1.0] - 2025-12-18

### Fixed

- Fixed typo in `run.sh` causing `jq` errors for `unifi_controller_username`.

## [1.0.8] - 2025-12-18

### Changed

- Added debug logging for file existence in `/config` and `/share` to troubleshoot mounting issues.

## [1.0.6] - 2025-12-18

### Changed

- Expanded search locations for `gcp-credentials.json` to include `/config`, `/share`, and `/homeassistant`.

## [1.0.5] - 2025-12-18

### Removed

- Removed 27 unused files from codebase cleanup (~135MB saved)
- Removed legacy STT/TTS modules (`stt.py`, `stt_picovoice.py`, `tts_*.py`, `wake_word.py`)
- Removed old boot script (`Boot_Jarvis.py`) and legacy server code
- Removed embedded Piper voice models (114MB) - use external Piper addon instead
- Removed test scripts and temporary files

### Changed

- Streamlined codebase to 17 essential files
- TTS/STT now fully delegated to Home Assistant voice pipeline

---

## [1.0.4] - 2025-12-17

### Added

- GitHub repository hosting at `https://github.com/Iron-Matrix4/ha-addons`
- One-click "Add to Home Assistant" installation button
- Vertex AI setup documentation

### Changed

- Removed personal data from examples (generic names/addresses)
- Updated README.md with comprehensive documentation

---

## [1.0.3] - 2025-12-17

### Added

- Custom Jarvis AI icon
- Documentation overhaul with feature tables and architecture diagram

---

## [1.0.2] - 2025-12-16

### Added

- UniFi Controller integration (DHCP leases, port forwards, firewall rules)
- Camera snapshot analysis using Gemini Vision
- Advanced network queries (bandwidth, device status)

---

## [1.0.1] - 2025-12-15

### Added

- Google Calendar integration (add events, list schedule)
- Location-based reminders ("Remind me when I get home")
- Timer functionality

---

## [1.0.0] - 2025-12-14

### Added

- Initial release of Jarvis AI Conversation Agent
- Wyoming protocol integration for Home Assistant voice pipeline
- Gemini AI-powered natural language understanding
- Smart home control (lights, switches, climate, covers, locks)
- Spotify integration via Spotcast
- Media management (Radarr, Sonarr, Prowlarr)
- qBittorrent download monitoring
- Google Custom Search for web queries
- Google Maps travel time calculations
- Weather queries via OpenMeteo
- Persistent memory system for user preferences
- J.A.R.V.I.S. personality and conversation style
