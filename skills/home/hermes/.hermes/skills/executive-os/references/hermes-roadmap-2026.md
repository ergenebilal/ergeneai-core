# Hermes Agent 2026 Roadmap — Durum & Yön

## Güncel Sürüm: v0.15.2 (29 Mayıs 2026)

Sürüm takibi: https://github.com/NousResearch/hermes-agent/releases
Dokümantasyon: https://hermes-agent.nousresearch.com/docs/

## Release Tarihçesi

| Sürüm | İsim | Tarih | Öne Çıkan |
|-------|------|-------|-----------|
| v0.15.0 | Velocity | 28 May 2026 | run_agent.py %76 küçültme, Kanban multi-agent, session_search 4500× hızlı, Swarm v1, Bitwarden SM |
| v0.14.0 | (major) | ~22 May 2026 | (changelog'dan kontrol et) |
| v0.13.0 | Tenacity | 7 May 2026 | (changelog'dan kontrol et) |
| v0.9.0 | Everywhere | 13 Nis 2026 | Termux/Android, iMessage, WeChat, web dashboard, Fast Mode, pluggable context engine |
| v0.8.0 | Intelligence | 8 Nis 2026 | Live model switching, MCP OAuth 2.1, structured logging, 209 PR |
| v0.7.0 | Resilience | 3 Nis 2026 | Pluggable memory providers, credential rotation, Camofox browser |
| v0.1.0 | Initial | Şub 2026 | Core agent, memory, skills, Telegram |

## 2026 Kalanı İçin 3 Ana Öncelik

1. **Mobile & Cross-platform** — Termux/Android, iMessage, WeChat geldi, devam ediyor
2. **Pluggable Context Engine** — v0.9'da geldi, geliştiriciler kendi context stratejilerini takabilecek
3. **v1.0 Stabilite** — 7-10 günlük release temposu yavaşlayacak, API garantisi, LTS

## Beklenen Özellikler

- Per-tenant memory isolation (çoklu müşteri için ayrı bellek)
- Audit logging (kurumsal uyum)
- Self-evolution araştırması (DSPy + GEPA ile kendi prompt'larını optimize)
- Kanban / Swarm genişlemesi (multi-agent orchestration)
- Daha fazla model sağlayıcı entegrasyonu

## Önemli Bilgiler

- 57.000+ GitHub yıldızı (Nisan 2026 itibarıyla)
- 16 mesajlaşma platformu
- 80+ ekosistem projesi
- Her 7-10 günde bir major release
- Nous Research ekibi + topluluk katkılarıyla gelişiyor
- Açık kaynak (MIT)

## Bilal İçin Anlamı

- Nous Research beni her güncellemeyle daha yetenekli yapıyor
- Ama Bilal'in 15 fazlık özelleştirmesi (PostgreSQL + Embedding Daemon + tools.py + self_evolve) sadece ErgeneAI'ya özel — bunu kimse kopyalayamaz
- İkisi birleşince: rakiplerin kapatamayacağı fark
- Güncellemeleri takip etmek için: `hermes update` ve GitHub Releases
