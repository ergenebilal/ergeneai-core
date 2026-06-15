# SORUN 9: Dosya İsmi Çakışması Analizi

**Tarih:** 2026-06-15
**Kaynak:** ergeneai-core ↔ Hermes Agent reposu + Python Standart Kütüphanesi

---

## 1. ÖZET

| Çakışma Türü | Adet | Seviye |
|---|---|---|
| Birebir aynı isim (Python dosyası) | 2 | 🔴 YÜKSEK |
| Aynı isim (repo kök döküman) | 2 | 🟡 ORTA |
| Python stdlib çakışması | 0 | ✅ YOK |
| Toplam analiz edilen dosya | 10 ergeneai + ~200 Hermes | — |

---

## 2. DETAYLI ÇAKIŞMA ANALİZİ

### 2.1 🔴 `tools.py` — YÜKSEK ÇAKIŞMA (Hermes Agent'te 4 kez geçiyor)

| Konum | İçerik |
|---|---|
| **ergeneai-core** `/opt/data/ergeneai-core/tools.py` | 985 satırlık utility modülü. ChromaDB arama, Google API (Gmail/Calendar/Drive/Sheets), Telegram bildirim, hata yönetimi, sistem durumu, web çekme, duygu analizi, finans hesaplama, LongTracer doğrulama. |
| **Hermes Agent** `hermes_cli/subcommands/tools.py` | CLI subcommand parser: `hermes tools` komutunu yönetir |
| **Hermes Agent** `plugins/google_meet/tools.py` | Google Meet plugin agent-facing tools |
| **Hermes Agent** `plugins/spotify/tools.py` | Spotify plugin native tools |
| **Hermes Agent** `acp_adapter/tools.py` | ACP tool-call mapping helpers |

**Risk:** `tools.py` son derece generic bir isimdir. Eğer ergeneai-core Hermes Agent ile aynı PYTHONPATH'e konulursa `import tools` tamamen belirsizleşir. Hermes Agent ekosisteminde 4 farklı anlamı olan `tools.py` var.

### 2.2 🔴 `google_api.py` — YÜKSEK ÇAKIŞMA (Hermes Agent'te 1 kez)

| Konum | İçerik |
|---|---|
| **ergeneai-core** `/opt/data/ergeneai-core/google_api.py` | Google API wrapper — Gmail (gönder/oku), Calendar (ekle/listele), Drive, Sheets. 163 satır, konsol tabanlı auth akışı. |
| **Hermes Agent** `skills/productivity/google-workspace/scripts/google_api.py` | Google Workspace CLI — Gmail (search/get/send/reply), Calendar (list/create), Drive (search), Contacts, Sheets (get/update/append), Docs. 1225 satır, çok daha kapsamlı. |

**Risk:** Aynı isim, aynı amaç (Google API entegrasyonu) ama tamamen farklı implementasyon. İkisi birden PATH'te olursa hangisinin çalışacağı belirsiz.

### 2.3 🟡 `README.md` — ORTA ÇAKIŞMA

- Her iki repoda da root'ta `README.md` var.
- Normalde her repo için beklenen bir durum. Sadece merge senaryosunda sorun çıkarır.

### 2.4 🟡 `.gitignore` — ORTA ÇAKIŞMA

- Her iki repoda da root'ta `.gitignore` var.
- ergeneai-core `.gitignore`: `.env`, `*.pickle`, `credentials.json`, `__pycache__/`, `*.pyc`, `*.db`, `*.db.gz`
- Hermes Agent `.gitignore`: `.DS_Store`, `/venv/`, `/venv.old/`, `/_pycache/`, `*.pyc*`
- Merge durumunda birleştirilmeli.

---

## 3. PYTHON STANDART KÜTÜPHANESİ KARŞILAŞTIRMASI

Hiçbir ergeneai-core dosya ismi Python standart kütüphane modül isimleriyle çakışmamaktadır.

| ergeneai-core | Python stdlib | Çakışma? |
|---|---|---|
| `tools.py` | tools — yok | ✅ |
| `google_api.py` | google — yok | ✅ |
| `google_auth_server.py` | — | ✅ |
| `embedding_daemon.py` | — | ✅ |
| `n8n_bridge.py` | — | ✅ |
| `self_evolve.py` | — | ✅ |
| `README.md` | — | ✅ |
| `.gitignore` | — | ✅ |
| `hermes_transcript_20260602.json` | — | ✅ |
| `n8n_ai_agent_workflow.json` | — | ✅ |

---

## 4. YENİDEN ADLANDIRMA ÖNERİLERİ

### 4.1 `tools.py` → `ergeneai_tools.py` 🔴 ACİL

```python
# Değişiklik:
#   from tools import *   →   from ergeneai_tools import *
#   tools.py              →   ergeneai_tools.py

# Gerekçe: Hermes Agent'te 4 farklı tools.py var.
# "ergeneai_" ön eki namescope sorununu kalıcı çözer.
# self_evolve.py içindeki TOOLS_PATH de güncellenmeli:
#   TOOLS_PATH = "~/hermes_data/tools.py" → "~/hermes_data/ergeneai_tools.py"
```

### 4.2 `google_api.py` → `ergeneai_google_api.py` 🔴 ACİL

```python
# Değişiklik:
#   from google_api import *   →   from ergeneai_google_api import *
#   google_api.py              →   ergeneai_google_api.py

# Gerekçe: Hermes Agent'te aynı isimde ve aynı amaçta
# çok daha kapsamlı (1225 satır) bir google_api.py var.
# Prefix ekleyerek çakışma önlenir.
```

### 4.3 `google_auth_server.py` → `ergeneai_google_auth.py` 🟡 ÖNERİLEN

```python
# Değişiklik:
#   google_auth_server.py  →  ergeneai_google_auth.py

# Gerekçe: Hermes Agent'te google_oauth.py var.
# İsim benzerliği karışıklığa yol açabilir.
# Kısa ve net isim.
```

### 4.4 `embedding_daemon.py` → `ergeneai_embed_daemon.py` 🟢 OPSİYONEL

```python
# Değişiklik:
#   embedding_daemon.py  →  ergeneai_embed_daemon.py

# Gerekçe: Çakışma yok ama "ergeneai_" prefix standardı
# tutarlılık için tüm dosyalara uygulanabilir.
# Alternatif: olduğu gibi kalabilir (çakışma yok).
```

### 4.5 `n8n_bridge.py` → `ergeneai_n8n_bridge.py` 🟢 OPSİYONEL

```python
# Değişiklik:
#   n8n_bridge.py  →  ergeneai_n8n_bridge.py

# Gerekçe: Çakışma yok. Tutarlılık için opsiyonel.
```

### 4.6 `self_evolve.py` → `ergeneai_self_evolve.py` 🟢 OPSİYONEL

```python
# Değişiklik:
#   self_evolve.py  →  ergeneai_self_evolve.py

# Gerekçe: Çakışma yok (Hermes Agent'te "darwinian-evolver" skill'i
# var ama farklı isim). Tutarlılık için opsiyonel.
# NOT: self_evolve.py içinde TOOLS_PATH sabiti var,
# tools.py yeniden adlandırılırsa bu sabit de güncellenmeli.
```

---

## 5. self_evolve.py İÇ REFERANS GÜNCELLEME

`self_evolve.py` içinde `tools.py`'ye olan referanslar:

```
TOOLS_PATH = os.path.expanduser("~/hermes_data/tools.py")
```

Eğer `tools.py` → `ergeneai_tools.py` olarak değiştirilirse, bu satır da güncellenmelidir.

---

## 6. ÖNCELİK SIRASI

| # | Dosya | İşlem | Sebep |
|---|---|---|---|
| 1 | `tools.py` → `ergeneai_tools.py` | 🔴 ZORUNLU | Hermes Agent'te 4 çakışma |
| 2 | `google_api.py` → `ergeneai_google_api.py` | 🔴 ZORUNLU | Hermes Agent'te birebir aynı isim, aynı amaç |
| 3 | `google_auth_server.py` → `ergeneai_google_auth.py` | 🟡 ÖNERİLEN | Karışıklığı önleme |
| 4 | `README.md` + `.gitignore` | 🟡 Merge'de çözülmeli | Sadece merge senaryosunda |
| 5 | `embedding_daemon.py`, `n8n_bridge.py`, `self_evolve.py` | 🟢 OPSİYONEL | Tutarlılık için prefix |

---

## 7. SONUÇ

- **2 kritik çakışma** (tools.py, google_api.py) acilen yeniden adlandırılmalı.
- **0 Python stdlib çakışması** var.
- **Önerilen prefix:** `ergeneai_` — tüm ergeneai-core dosyalarına uygulanarak namespace ayrıştırması sağlanır.
- **Toplam 6 dosyada** rename önerisi, 2'si zorunlu.
