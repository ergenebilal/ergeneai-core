# HKUDS/Nanobot Kurulum ve Yapılandırma Notları

## Versiyon Geçmişi
- **Eski:** nanobot-ai v0.2.0 (obot-platform, Go'a geçmiş, Python versiyonu terk edilmiş, SSRF CVE var)
- **Yeni:** HKUDS/nanobot v0.2.1 (43.5k star, 2.766 commit, Python 3.11+, MIT lisansı, çok aktif)

## Kurulum
```bash
cd /home/hermes
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip3.11 install -e .
```

## Systemd Servisi
```ini
[Unit]
Description=Nanobot AI Agent Gateway (HKUDS)
After=network.target

[Service]
Type=simple
User=hermes
WorkingDirectory=/home/hermes/nanobot
ExecStart=/home/hermes/.local/bin/nanobot gateway --port 18790
Restart=on-failure
RestartSec=5
Environment=HOME=/home/hermes

[Install]
WantedBy=multi-user.target
```

Not: `/etc` read-only mount. Servis dosyası `sudo tee` ile yazılır.

## Önemli Notlar
- Config: `~/.nanobot/config.json` (eski config'le uyumlu)
- Provider: DeepSeek hazır, Codex OAuth hazır, GitHub Copilot OAuth hazır
- Gateway port: 18790 (localhost)
- RAM kullanımı: ~71MB
- /usr read-only → script'ler ~/.local/bin/ altında olmalı

## Lisans
MIT License — ticari kullanım, değiştirme, satış serbest. Tek şart: lisans metnini korumak.
