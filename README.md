# ErgeneAI — Hermes Backup

**Tarih:** 03.06.2026
**Backup nedeni:** Tüm Hermes yapılandırmasının GitHub'a yedeklenmesi.

## İçerik

| Klasör | Açıklama |
|--------|----------|
| `hermes_data/` | Ana kod: tools.py, hermes_brain_core.py, self_evolve.py, embedding_daemon.py |
| `hermes_data/tests/` | 220 test (test_tools.py Phase 1-4 + test_hermes_brain_core.py) |
| `skills/` | Hermes skill'leri (9 adet: gsd, executive-os, digital-menu, dogruluk, financial, etc.) |
| `gsd/` | Get-Shit-Done Redux framework (33 agent, 88 workflow) |
| `n8n/` | n8n workflow yedekleri (IG DM asistanı, AI Bülten) |
| `opt/` | Stratejik belgeler (finansal plan, nanobot spec, AI VFX roadmap) |
| `config/` | Hermes konfigürasyonu (config.yaml, crontab) |

## Önemli Notlar
- `.env` dosyası ve secret'lar yedeklenmemiştir
- Google OAuth token'ları (`token.pickle`) yedeklenmemiştir
- n8n API'a erişilemediği için workflow JSON'ları eksik olabilir
- PostgreSQL veritabanı yedeklenmemiştir (schema docs'ta)

## Geri Yükleme
```bash
git clone git@github.com:ergenebilal/ergeneai-core.git
cd ergeneai-core
cp hermes_data/*.py /home/hermes/hermes_data/
cp -r skills/* /home/hermes/.hermes/skills/
```
