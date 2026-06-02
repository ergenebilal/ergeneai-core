# System Maintenance Playbook — Cron Auditing & Optimization

## Cron Audit Flow (Kanıtlanmış Yöntem)

### 1. Inventory
```
cronjob(action='list') → tüm crons'ları dök
```
Not: Zaman damgalarını mutlaka kontrol et. Sunucu UTC'deyse, TR saati için +3 ekle.

### 2. Analyze Redundancies
Şu soruları sor her cron için:
- **Çakışma var mı?** Aynı saatte çalışan birden fazla cron → yay veya birleştir
- **Neredeyse aynı iş yapan var mı?** (örn. 2 GitHub taraması) → birini tut, ötekini sil
- **Kullanıcı bu saatte müsait mi?** Kurye saatleri (08:00-18:00 TR) bildirim okunmaz
- **Çıktı gidiyor mu yoksa local'de mi kalıyor?** "deliver: origin" ama kullanıcı uyuyorsa anlamsız
- **Son çalışması hata vermiş mi?** Hatalı cron temizlenmeli veya düzeltilmeli

### 3. Timezone Verification
```
date -u                    → UTC saati
TZ=Europe/Istanbul date    → TR saati
```
Her cron'un UTC schedule'ını kontrol et:
- `0 6 * * *` = 06:00 UTC = 09:00 TR ✅ (sabah)
- `30 5 * * *` = 05:30 UTC = 08:30 TR ✅ (sabah erken)
- `0 19 * * *` = 19:00 UTC = 22:00 TR ✅ (akşam)

### 4. Classification
| Tür | Açıklama | Varsayılan |
|-----|----------|------------|
| **Kullanıcıya bildirim** | Sabah check-in, finans raporu, hatırlatıcı | deliver: telegram |
| **Sistem bakımı** | Bellek yedekleme, rüya seansı, ECC güncelleme | deliver: local |
| **Watchdog** | MCP, Nanobot servis izleme | every 5dk, deliver: local |
| **Araştırma** | GitHub taraması, Hermes güçlenme | Kullanıcıya, akşam saatinde |

### 5. Batch Operations
Benzer crons'ları grupla ve toplu işlem yap:
1. Önce **silinecekleri** toplu sil (en fazla 4-5 aynı anda)
2. Sonra **saat düzeltilecekleri** update et
3. En son **yenileri** oluştur

### Cron Schedule Update — PITFALL (next_run_at recalculates)

**Problem:** When you update a cron job's `schedule` via `cronjob(action='update')`, the system recalculates `next_run_at` from **current time**, not from the last run. This means:

- If it's 17:07 UTC and you set schedule to `30 17 * * *`, next_run_at = **today 17:30** (not tomorrow)
- Result: the job fires AGAIN today, on top of its earlier run

**Fix — Two methods:**

**Method A (ISO timestamp → recurring):**
```
1. Remove the old job
2. Create with ISO schedule for tomorrow: schedule='2026-06-02T17:30:00'
   → next_run_at = tomorrow 17:30 ✅
3. Immediately update to recurring: schedule='30 17 * * *', repeat=0 (forever)
   → next_run_at stays at tomorrow 17:30 (preserved from ISO create)
```

**Method B (pause + resume cron):**
```
1. Pause the job with cronjob(action='pause')
2. Schedule a one-shot resume cron for the desired start day:
   cronjob(action='create', schedule='31 5 * * 2' etc., prompt='Resume job_id X')
3. The resume cron fires at 05:31 UTC, job resumes, next_run_at recalculates
```

**Method A is simpler.** Method B is backup if ISO timestamp doesn't preserve.

### 6. Post-Cleanup Verification
- Toplam cron sayısını not et (örn. 20 → 13)
- Yarın ilk çalışacak cron'u kontrol et (next_run_at)
- "last_status: error" olan cron kalmadı mı kontrol et

### 7. Cron Job Creation Checklist — MUST-SET FIELDS

Yeni bir cron oluştururken şu üç alanı ASLA atlama:

**1. `workdir` — critical for module imports**
Cron'un prompt'u `tools.pg_son()` gibi custom bir modül çağırıyorsa, workdir o modülün bulunduğu dizine ayarlanmalı:
```
cronjob(action='create', workdir='/home/hermes/hermes_data', ...)
```
Workdir'siz cron'lar `ModuleNotFoundError` ile sessizce çöker (kullanıcıya hiçbir şey gelmez, sadece `last_status: error` kalır).

**2. `skills` — critical for agent context**
Cron agent'ının ne yapacağını bilmesi için ilgili skill'leri ekle. En azından `gsd`:
```
cronjob(action='create', skills=['gsd'], ...)
```
Skills'siz cron'lar Genel AI gibi davranır — prompt'ta belirtilen spec'i takip etmez, kısayollara kaçar veya eksik çıktı üretir.

**3. `schedule` — TR timezone convention**
Kullanıcının profili "tüm cron'lar TR saatinde" der. Sistem Europe/Istanbul olduğu için cron schedule değerleri ZATEN TR saatidir. UTC'ye çevirme YAPMA:
- `"30 8 * * *"` = 08:30 TR (doğru, UTC'ye çevirme)
- `"0 9 * * *"` = 09:00 TR (doğru, 06:00 UTC sanıp düzeltme)

**Tipik cron saatleri (TR):**
| Saat | Cron Türü | Açıklama |
|------|-----------|----------|
| 06:00 | 🔔 Hatırlatıcı | Sabah erken rutin |
| 08:30 | ☀️ Proaktif Brifing | AI analizi + strateji |
| 09:00 | 💰 Finans Check-in | Borç/gelir takibi |
| 14:00 (Pzt) | 📅 Haftalık Toplantı | Stratejik değerlendirme |

### 8. Silent Failure Diagnosis

Bir cron hiç çalışmamış gibi görünüyorsa (`last_run_at: null`, kullanıcıya hiçbir şey gelmemiş):

```
cronjob(action='list') → kontrol et:
  1. last_run_at: null ise → hiç tetiklenmemiş
     → workdir eksik mi? skills eksik mi?
  2. last_status: "error" ise → tetiklenmiş ama patlamış
     → prompt'ta hatalı komut/tool çağrısı var mı?
  3. next_run_at geçmişteyse → scheduler takılmış
     → cronjob(action='run') ile manuel test et, çıktıyı gör
```

**En sık 3 sessiz ölüm sebebi:**
1. **workdir yok** — cron `tools.py`'ı import edemez, sessizce çöker
2. **skills yok** — cron agent'ı ne yapacağını bilmez, boş/pas geçer
3. **schedule UTC sanılmış** — 3 saat erken/geç çalışır, kullanıcı cevabı görmez

## Component Retirement Procedure (Broken Service Decommission)

Use when a system component is broken, deprecated, or being replaced by a working alternative.

### Steps

1. **Verify replacement works**
   - Test the replacement service/function independently
   - Confirm data integrity between old and new paths
   - Example: ChromaDB → PostgreSQL+Embedding Daemon

2. **Redirect all code paths**
   - Find every reference to the old component in code (`search_files(target='content', pattern='old_component')`)
   - Update function calls, import paths, and constants
   - Example: `beyin_ara()` → internally calls `pg_ara_vector()` instead of ChromaDB

3. **Remove from health checks**
   - Edit `collect_runtime_health_components()` in `hermes_brain_core.py` to drop the dead component
   - Re-run `run_brain_health_report()` → verify "broken": []

4. **Clean up disk space**
   - Remove dead component's cache: `~/.cache/<component>/`
   - Remove dead component's Python package: `pip uninstall <package>`
   - Remove any stale model downloads, logs, or temp files

5. **Update monitoring scripts**
   - If cron watchdogs or dashboards reference the old component, update them
   - Re-run `hermes_durum` to confirm "healthy"

6. **End-to-end verification**
   - Call every function that was redirected and confirm it works
   - Verify the health report shows 0 broken components

## Global Script Installation (/usr is Read-Only Workaround)

When `/usr/local/bin` is mounted read-only (`ro`), use this workaround:

1. **Use ~/.local/bin** — already in `$PATH`, user-writable
2. **Script must cd to working dir first:** `cd /home/hermes/hermes_data && python3.11 -c "..."` — avoids PYTHONPATH and venv path issues
3. **Use system python3.11** — the venv (`/opt/hermes/venv/bin/python`) may lack `sentence_transformers` and `psycopg2`; `python3.11` from system has them in `~/.local/lib/python3.11/site-packages/`
4. **Test immediately** after creating each script
5. **Update .bashrc aliases** to match the same approach (but note: terminal tool may use non-interactive shell that skips .bashrc)

## Disk Deep-Clean Procedure

When disk is above 90%, use this measured cleanup:

### Safe-to-Delete Candidates (with sizes)
| Path | Typical Size | Risk |
|------|-------------|------|
| `~/.cache/ms-playwright/` | 1.3 GB | Safe — browser binaries, not needed for model inference |
| `~/.cache/huggingface/hub/models--*` (unused) | 1-2 GB | Medium — check which model is active first |
| `~/.cache/pip/` | 80-100 MB | Safe |
| `~/.cache/npm/` (`.npm/`) | 50-100 MB | Safe |
| `/var/log/*.gz`, `*.old`, `*.1`, `*.2`, `*.3` | 50-150 MB | Safe |
| `apt-get clean` | 100-200 MB | Safe |
| `pip uninstall <unused>` | 50-200 MB each | Check usage first |

### Active Model Protection
Before deleting HF models, identify the active embedding model:
```bash
grep "SentenceTransformer" embedding_daemon.py
# → paraphrase-multilingual-MiniLM-L12-v2 → KEEP this one
# Delete all others
```

### Measurement Protocol
```bash
# Before
df -h / | tail -1
# After each step
echo "Freed: $(df -h / | tail -1 | awk '{print $5}') used"  
# Final diff
df -h / | tail -1
```

### Disk Safety Rule
- Docker containers in active use: **do not prune**
- Active model weights: **do not delete** (embedding daemon will crash)
- Python venv packages: **check imports first** before uninstalling

## Bilal'in Optimize Edilmiş Cron Takvimi (TR Saati)

| Saat (TR) | Cron | Tip |
|---|---|---|
| **08:30** 🛵 | ☀️ Sabah Check-in | Kullanıcı |
| **09:00** 🛵 | 🔔 Denetim Hatırlatıcı | Kullanıcı |
| **09:00** 🛵 | 🤖 Hermes-Nanobot Sink. | Kullanıcı |
| **09:00** 🛵 | 💰 Günlük Finans + Fırsat | Kullanıcı |
| **14:00** 🛵 | 📬 ErgeneAI Bülten | Local |
| **17:00** 🛵⬅️ | 🏆 GitHub Fırsat | Kullanıcı |
| **20:00** 🏠 | 🧠 Hermes Güçlenme | Kullanıcı |
| **21:00** 🏠 | 📊 KPI + Öz Eleştiri | Kullanıcı |
| **22:00** 🏠 | 🌙 Akşam Check-in | Kullanıcı |
| **00:00** 🌃 | 🌙 Rüya Seansı | Local |
| **03:00** 🌃 | 🧠 Bellek Yedekleme | Local |

**Sistem (sessiz):** MCP Watchdog (5dk), Nanobot Watchdog (5dk), ECC Haftalık (Pzt 07:00)
