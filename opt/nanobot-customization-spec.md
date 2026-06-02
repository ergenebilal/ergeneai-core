# Codex Spec: ErgeneAI Nanobot Customization Plan

## Target Product
Özelleştirilmiş `HKUDS/nanobot` (v0.2.1) — müşteriye satılabilir AI ajan framework'ü.

## Current State (already done by Hermes)
- Eski `nanobot-ai v0.2.0` kaldırıldı
- `HKUDS/nanobot` /home/hermes/nanobot/ kuruldu, editable mode
- systemd service aktif (port 18790)
- Provider: DeepSeek, Codex OAuth, GitHub Copilot OAuth hazır
- 71.4MB RAM, gateway çalışıyor

## Customization Tasks (for Codex)

### 1. Branding Layer (white-label)
- Replace "🐈 nanobot" with custom branding in CLI output
- Add ErgeneAI/ErgeneAI client branding config
- Make gateway response headers customizable

### 2. Provider Config per Customer
Config file: `~/.nanobot/config.json`
- Default provider: DeepSeek
- Allow overriding provider/model per config
- Add API key field for external access

### 3. Tool Restrictions (SaaS packaging)
- Create customer tier config: `basic`, `pro`, `enterprise`
- Restrict tools based on tier
- Basic: WhatsApp/Telegram messaging only
- Pro: + MCP tools, web search
- Enterprise: full access (as-is)

### 4. Simple Onboarding Flow
- `nanobot onboard` should:
  - Ask: customer name, tier, provider
  - Generate branded config
  - Print access URL + API key
  - Start gateway automatically

### 5. API Wrapper
- Simple Flask/FastAPI wrapper for dashboard
- Endpoints:
  - /health → system status
  - /config → customer config (tier info)
  - /metrics → usage stats

### 6. Install Script for Customer
- Single curl command (like Hermes install)
- `curl -fsSL https://setup.ergeneai.xyz/install.sh | bash`
- Auto-configures everything

## Pricing Model (for UI/config)
| Tier | Price | Features |
|---|---|---|
| Basic | 1.500₺ | WhatsApp/Telegram AI, 1 provider, no MCP |
| Pro | 3.000₺ | + MCP tools, web search, custom branding |
| Enterprise | 5.000₺ | Full access, white-label, dedicated support |

## Architecture Notes
- Python 3.11, asyncio
- Config: `~/.nanobot/config.json`
- Gateway: port 18790
- All changes must be in `/home/hermes/nanobot/`
- Test before deploying: `pytest tests/`

## Development Flow
1. Codex implements changes
2. Hermes tests and verifies
3. If OK → systemctl restart nanobot
4. If fail → rollback with git checkout
