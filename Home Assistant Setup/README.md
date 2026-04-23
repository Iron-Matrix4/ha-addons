# 🏠 Home Assistant Setup & SSH Keys

**Last Updated:** 2026-04-23
**Primary Instance:** [YOUR_HA_IP]

---

## 🛠️ System Overview

### Core Infrastructure
- **Host:** Remote Home Assistant Instance
- **IP Address:** `[YOUR_HA_IP]`
- **Domain:** [YOUR_DOMAIN] (via Cloudflare Tunnel)
- **Primary AI:** Gemini Vision AI (for security and event summaries)

### Key Add-ons
| Add-on | Purpose |
| :--- | :--- |
| **Terminal & SSH** | Secure shell access for management. |
| **Jarvis AI** | Custom AI assistant integration (Vision/Voice). |
| **Frigate** | NVR for Unifi Cameras with object detection. |
| **Overseerr/Plex** | Media management stack. |

---

## 🔑 SSH Configuration

The SSH keys are used for remote management, debugging, and automated scripting (e.g., Jarvis AI integration).

### Key Files
**Location:** `PATH-TO-KEYS\ssh_keys\`

- **Private Key:** `ha_key` (Used for authenticating to the HA instance)
- **Public Key:** `ha_key.pub`
- **Type:** `ED25519`
- **Comment:** `ssh-key`

### Public Key Content
```text
ssh-ed25519 [YOUR_PUBLIC_KEY] antigravity
```

### Usage
To connect to the Home Assistant instance from a terminal:
```powershell
ssh -i "PATH-TO-KEYS\ssh_keys\ha_key" root@[YOUR_HA_IP]
```

---

## 🤖 Jarvis AI Integration
- **Wake Word:** Configured in HA with random audio responses ("Yes sir?", "At your service.", etc.)
- **Pipeline:** Uses `tts.piper` for speech synthesis.
- **Token:** Long-lived access token (stored in `jarvis_ai/1`).

---

## 📋 Automation Summary
- **Security:** Garden motion analysis via Gemini.
- **Presence:** `zone.lb_ha` for Home/Away modes.
- **Environmental:** Auto blinds (>35°C), Arlo's fan (>23°C), Pond water level alerts.
- **Media:** Plex server automation and Ombi/Overseerr notifications.
