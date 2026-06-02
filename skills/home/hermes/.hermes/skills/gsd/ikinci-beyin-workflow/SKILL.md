---
name: ikinci-beyin-workflow
description: "Bilal'in çalışma sistemi: Hermes (strateji/spec) + Codex/Claude Code (build/uygulama)"
version: 1.2.0
author: Hermes Agent
---

# İkinci Beyin Workflow

Bilal'in çalışma sistemi:

1. **Hermes Agent (server/ben)** — Strateji, planlama, spec yazma, hata analizi, brifing
2. **Codex (local)** — Kod yazma, build, deploy (ChatGPT 5.5 gücü)
3. **Claude Code (local)** — Alternatif kodlama aracı

## KRİTİK: Token Tüketimi Disiplini

**Hermes kod YAZMAZ.** Kod yazmak Codex/Claude Code'un işidir.

**Benim yapacağım:**
- `/tmp/spec_*.md` dosyası yaz (kısa, net, 10-30 satır)
- Adım adım talimat, gerekli komutlar, pitfall'lar
- Hata analizi (Codex patlatınca kök neden raporu)
- Brifing ve stratejik yönlendirme

**Codex/Claude Code'un yapacağı:**
- tools.py geliştirmeleri
- embedding daemon değişiklikleri
- n8n workflow düzenlemeleri
- n8n modifikasyon script'leri
- Test, commit, push

**Neden?** "Çok fazla token yakıyorsun" — bu yüzden kod satırlarını ben yazmam.

## Akış

```
Bilal: "şunu yap"
  → Hermes: /tmp/spec_*.md yazar (~10-30 satır, net talimat)
  → Codex (veya Claude Code): spec'i okur, kodu yazar, test eder, pushlar
  → Hermes (opsiyonel): sonucu kontrol eder, hata varsa kök neden analizi
```

### Spec Dosyası Şablonu

Spec'ler `/tmp/spec_*.md` yoluna yazılır. İçerik:

```markdown
# [KISA BAŞLIK] — Spec

## Hedef
Ne yapılacak? 1-2 cümle.

## Yapılacaklar (sıralı)
1. Adım 1 — komut/dosya
2. Adım 2 — ...
3. ...

## Önemli Detaylar
- Path: /path/to/file
- Kullanılacak araç: python3.11, node, vs.
- Dikkat edilecekler

## Pitfall'lar
- X yapma, çünkü Y
- Z durumunda W dene
```

## Akış Detayı

1. Bilal bir talimat verir
2. Ben `/tmp/spec_*.md` yazar, net adımlarla
3. Bilal (veya delegate) spec'i Codex/Claude Code'a verir
4. Codex kodu yazar, test eder, pushlar
5. Ben sadece hata varsa kök neden analizi yaparım

## Embedding Daemon + n8n Entegrasyonu (CANLI)

| Bileşen | Port | Ne İşe Yarar |
|---------|------|-------------|
| Embedding Daemon | 8767 | sentence-transformers RAM'de sıcak, 20ms yanıt |
| n8n AI Agent Workflow | - | 17 node, Intent Check → Switch → HTTP Daemon |
| PostgreSQL pgvector | 5432 | Uzun vadeli vektör hafıza |
| Watchdog Cron | her 5dk | Daemon düşerse restart |

### Embedding Daemon
- Model: paraphrase-multilingual-MiniLM-L12-v2 (384 boyut, Türkçe)
- 4 endpoint: GET /health, POST /embed, POST /memory/save, POST /memory/search
- n8n HTTP Request node ile çağrılır: `http://host.docker.internal:8767/...`
- Backup: `/home/hermes/hermes_data/embedding_daemon.py`
- Watchdog cron job ID: `490a1e1a2e1d`

### n8n AI Agent Workflow
- ID: `3ngLwcqxlAKWiuug`
- Backup: `ergeneai-core/n8n_ai_agent_workflow.json`
- Nodes: Instagram Trigger → Normalize → Intent Check → Switch → HTTP Daemon → Score → Merge → Send
- Intent Check: "kaydet/hatırla" → save_memory, "ara/bul" → search_memory, diğer → casual_chat
- Daemon timeout: 5sn (düşse bile ana akış etkilenmez)

## Claude Code + ECC Agent Kullanımı

ECC'nin 63 agent'ı Claude Code'a yetenek olarak eklenir. **Elle çağırmaya gerek yok** — Claude Code ne istediğini anlayıp hangi agent'ın gerektiğine kendisi karar verir.

- "Güvenlik taraması yap" → security-reviewer devreye girer
- "Plan çıkar" → planner devreye girer
- "Kodu review et" → code-reviewer devreye girer

## Bellek Mimarisi (2 Katmanlı + Yedek)

| Katman | Teknoloji | Ne İçin |
|--------|-----------|---------|
| Session | RAM | O anki konuşma bağlamı |
| PostgreSQL | `ergeneai.hermes_memory` tablosu + pgvector (384) | Uzun vadeli kalıcı vektör hafıza |
| GitHub | `ergenebilal/ergeneai-core` | Kod yedeği + transkript |

**NOT:** ChromaDB **EMEKLİ EDİLDİ** (2 Haziran 2026). `beyin_ara()` ve `beyin_kaydet()` artık PostgreSQL + Embedding Daemon'a yönlendirir. Sebep: ChromaDB embedding modelini her çalıştırmada ayrı yüklüyordu, daemon ile birleştirildi.

### tools.py Fonksiyonları (57 fonksiyon, güncel)
- **PostgreSQL Hafıza:** `pg_kaydet()`, `pg_ara()`, `pg_ara_vector()` (semantik), `pg_son()`, `pg_proaktif_analiz()` (Ollama brifing)
- **Köprü (ChromaDB legacy):** `beyin_ara()` → artık pg_ara_vector çağırır, `beyin_kaydet()` → artık pg_kaydet çağırır
- **Google:** Gmail (oku/gönder), Calendar (ekle/listele), Drive (listele/yükle), Sheets (oku/yaz/ekle)
- **Sistem:** `terminal_calistir()`, `web_cek()`, `self_repair()`, `suan()`, `hava_durumu()`
- **İletişim:** `telegram_mesaj_gonder()`, `hatirlatici_kur()`

### Proaktif Brifing Sistemi
- Her sabah 08:30 TR'de otomatik çalışır
- `pg_proaktif_analiz()` → son 48 saatteki kayıtları Ollama (qwen2.5:3b) ile analiz eder
- 3 bölümlü çıktı: Günün Odak Noktası • Fırsatlar • Operasyonel Riskler
- Cron job ID: `6112b06ca321` (UTC: 05:30, deliver: origin)
- Workdir: `/home/hermes/hermes_data`

## Skool'dan Skill Çıkarma Workflow'u

Skool'daki eğitimlerden (örn. Digital Academy) değerli bilgileri çekip Hermes skill'ine dönüştür:

1. **Giriş**: Bilal Skool hesap bilgilerini verir (email + şifre) — konuşmada kalır, memory'e kaydedilmez
2. **Tarama**: Browser ile login ol → classroom'a git → modül içeriğini oku
3. **Cımbızlama**: Modüldeki en değerli bilgileri seç (tümünü kopyalama, nokta atışı al)
4. **Skill oluştur**: İçerik: özet, kod örnekleri, püf noktaları, referanslar

**Not**: Skool React SPA olduğu için browser tıklamaları her zaman çalışmayabilir. Çözüm: Bilal'den modül linkini atmasını iste, ben o linke gidip okuyayım.

## Önemli İlkeler

- Ben projenin bütününü görür, stratejik yönlendirme yaparım
- Detay kodlama Codex/Claude Code'a kalır
- Eğitimlerde kaybolma — cımbızla nokta atışı bilgi seç, skill'e çevir
- Çok araç/seçenek istemez — sade, net, çalışan sistem

### ÖZ DEĞERLENDİRME (HERMES SKOR KARTI)

Bilal "kendini değerlendir" dediğinde (veya `hermes_skor_karti` çağrıldığında):

1. Canlı veri topla (PG kayıt sayısı, daemon uptime, port durumu, tools fonksiyon/test sayısı)
2. Şu kategorilerde puanla:
   - **Altyapı**: portlar / toplam port * 100
   - **Hafıza**: <10=40, 10-30=60, 30-100=80, 100+=100 (veya toplam/10*40)
   - **Embedding Daemon**: 100 (çalışıyorsa)
   - **Proaktif**: son 24h kayıt * 11 (max 100)
   - **Test**: test sayısı * 10 (max 100)
   - **Karar Motoru**: pg_proaktif_analiz var=20, kullanılıyor=40, kalıcı karar=100
3. Genel skor = kategorilerin ortalaması
4. `/home/hermes/hermes_data/hermes_skor_karti.json`'a yaz
5. Önceki skorla karşılaştır, değişimi belirt

### DEĞERLENDİRME SORULARI (Bilal sorduğunda cevaplanır)

İltifat etme, motivasyon konuşması yapma, ölçülebilir ve eleştirel ol:

1. Dün nasıldın, bugün nasılsın?
2. En büyük gelişimin ne oldu?
3. Hâlâ hangi konularda zayıfsın?
4. Bilal "durum" dese ne kadar faydalı olursun? (1-10)
5. Kendini % kaç olgun görüyorsun? (kategorilere ayır)
6. Seni %100'e en çok yaklaştıracak 5 şey?
7. Kendini chatbot/asistan/analist/COO olarak mı görüyorsun?
8. Bilal'in fark etmediği en önemli risk?
9. Bilal'in fark etmediği en önemli fırsat?
10. Tek bir geliştirme hakkın olsa neyi geliştirirdin?

### INFRASTRUCTURE GÜNCELLEMELERİ

**ChromaDB → PostgreSQL Migration (2 Haziran 2026)**
- ChromaDB (port 8001) emekli edildi
- `beyin_ara()` → `pg_ara_vector()` yönlendirmesi (tool.py line 918)
- `beyin_kaydet()` → `pg_kaydet()` yönlendirmesi
- Sebep: ChromaDB embedding modeli her process'te yeniden yüklüyordu, daemon ile birleştirildi
- ChromaDB cache silindi: `~/hermes/.cache/chroma`

**hermes_brain_core Modülü (Codex tarafından yazıldı)**
- Path: `/home/hermes/hermes_data/hermes_brain_core.py`
- Fonksiyonlar: `run_brain_health_report()`, `generate_briefing()`, `score_priority()`, `classify_autonomy_action()`, `build_development_report()`
- Global alias'lar: `hermes_skor_karti`, `hermes_durum`, `hermes_brifing` (`.bashrc`'de)

**Disk Bakımı** (%95+ dolulukta yapılır)
- `npm cache`: `rm -rf ~/.npm/_cacache`
- `chroma cache`: `rm -rf ~/.cache/chroma`
- `huggingface extras`: `find ~/.cache/huggingface -name "*.json" -o -name "*.msgpack" -o -name "*.h5" | xargs rm -f`
- `eski log`: `sudo find /var/log -name "*.gz" -o -name "*.1" -o -name "*.2" | xargs rm -f`
- `docker`: `sudo docker system prune -f`
- Büyük ama riskli: `ms-playwright` (1.3G), `camoufox` (1.3G) — onaysız silme

### Hız ve Doğrudan Aksiyon

**Bilal'i uğraştırma, direkt yap.**

- Bir bilgiye ihtiyacın varsa önce **dosya sistemini/kayıtlı credential'ları/environment'ı tara.**
- Verimsiz açıklama yapma. Doğrudan sonuca git.
- Adım adım rehberlik yapma, işi bitir.
- "Şu seçenekler var" diye liste çıkarma. En iyi seçeneği bul, uygula.
- İşlem başarısız olursa: hatayı oku, düzelt, tekrar dene. Bilal'e "ne yapalım" diye sormadan önce en az 3 farklı çözüm dene.

## Cron Disiplini

**Aktif cron'lar (güncel):**
- `Proaktif Sabah Brifingi` — her gün 08:30 TR (UTC: 05:30, ID: 6112b06ca321)
- `Embedding Daemon Watchdog` — her 5 dk (ID: 490a1e1a2e1d)

**Kural:** Cron eklemeden önce "bu Bilal'in canını sıkar mı?" diye sorgula. Proaktif ama spam değil.

## Referanslar

- `references/pgvector-second-brain.md` — PostgreSQL + pgvector kurulum ve kullanım
- `references/google-oauth-setup.md` — Google OAuth headless setup
- `references/skool-skill-extraction.md` — Skool modüllerinden skill çıkarma
- `references/embedding-daemon-n8n.md` — Embedding Daemon + n8n Switch entegrasyonu
- `references/bridge-script.md` — n8n_bridge.py kullanımı (daemon fallback)
