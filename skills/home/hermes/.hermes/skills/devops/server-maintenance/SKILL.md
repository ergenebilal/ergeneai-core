---
name: server-maintenance
version: 1.0.0
author: Hermes Agent
description: Hermes sunucusunda disk temizliği, global komut kurulumu, servis sağlığı ve bileşen emeklilik prosedürleri. Ubuntu 22.04, /usr read-only.
---

# Server Maintenance

## When to Use

- Disk doluluğu şikayeti (%90+), "df -h" çağrısı
- "command not found" hatası alan bir alias/script kurulumu
- Servis sağlığı sorgulama ("hermes_durum", status check)
- Eski/kırık bir bileşeni emekli etme ihtiyacı
- Sunucu bakım/temizlik talebi

## Disk Temizlik Prosedürü

### Önce ne kadar alan var?

```bash
df -h /
```

### Güvenli Temizlik Listesi (Öncelik Sırası)

| Ne | Tipik Boyut | Güvenli mi? |
|---|---|---|
| `~/.cache/ms-playwright/` | 1.3 GB | ✅ Browser binary'leri, AI işi için gerekli değil |
| `~/.cache/huggingface/hub/` içinde **kullanılmayan** modeller | ~1 GB | ✅ Model bazlı kontrol et |
| `~/.cache/pip/` | ~80 MB | ✅ pip her zaman yeniden indirir |
| `~/.npm/` | ~100 MB | ✅ npm her zaman yeniden indirir |
| `/var/log/*.gz, *.1, *.2, *.3` | ~150 MB | ✅ Eski sıkıştırılmış loglar |
| `sudo apt-get clean` | ~100 MB | ✅ Paket cache |
| Playwright Python paketi (`pip3 uninstall playwright`) | 136 MB | ✅ Kullanılmıyorsa |

### Embedding Modeli — SAKIN SİLME

Aktif model: `sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2` (~458 MB)
→ Embedding Daemon (port 8767) için hayati. Silersen embedding işlemez.

### Toplu Temizlik Komutu

```bash
# Safe cleanup (run as hermes user)
rm -rf ~/.cache/ms-playwright/
rm -rf ~/.cache/pip/
rm -rf ~/.npm/
sudo find /var/log -name "*.gz" -o -name "*.old" -o -name "*.1" -o -name "*.2" -o -name "*.3" | sudo xargs rm -f
sudo apt-get clean -y
```

### HF Model Ayıklama (sadece kullanılmayanları sil)

```bash
# Önce aktif modeli bul
grep -i "sentence-transformers\|model" /home/hermes/hermes_data/embedding_daemon.py | head
# Sonra kullanılmayanları sil (aktif olanı KORU)
rm -rf ~/.cache/huggingface/hub/models--cross-encoder--*
rm -rf ~/.cache/huggingface/hub/models--emrecan--*
rm -rf ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2
rm -rf ~/.cache/huggingface/hub/models--Systran--faster-whisper-*
```

### Python Yolu: System python3.11 vs Venv

**KRİTİK:** `tools.py`'nin bağımlılıkları (`sentence-transformers`, `psycopg2-binary`) **system python3.11**'de kurulu (`~/.local/lib/python3.11/site-packages/`). `/opt/hermes/venv/`'de bu paketler YOK.

Bu yüzden `hermes_durum` gibi script'lerde python yolu:
```bash
# ✅ DOĞRU — system python3.11 kullan (paketler burada)
cd /home/hermes/hermes_data && python3.11 -c "from hermes_brain_core import run_brain_health_report; ..."

# ❌ YANLIŞ — venv python'da psycopg2/sentence-transformers yok
PYTHONPATH=/home/hermes/hermes_data /opt/hermes/venv/bin/python -c "..."
```

Eğer venv'e kurulum gerekirse:
```bash
/opt/hermes/venv/bin/pip install psycopg2-binary sentence-transformers
```
Ama bu yavaş olabilir. System python3.11 daha güvenilir.

### Script içinde kullanım (önerilen):
```bash
cat > ~/.local/bin/hermes_durum << 'SCRIPT'
#!/bin/bash
cd /home/hermes/hermes_data && python3.11 -c "
from hermes_brain_core import run_brain_health_report
import json
print(json.dumps(run_brain_health_report(), indent=2, ensure_ascii=False))
"
SCRIPT
chmod +x ~/.local/bin/hermes_durum
```

### Global Komut Kurulumu

### Sorun: /usr/local/bin Read-Only

Bu sunucuda `/usr` read-only mount edilmiştir:

```
/dev/sda2 on /usr type ext4 (ro,relatime)
```

Bu yüzden `/usr/local/bin/` yazılamaz. `sudo tee` ve `sudo chmod` çalışmaz.

### Çözüm: ~/.local/bin Kullan

`~/.local/bin` zaten PATH'te ve writable'dır.

```bash
# Script oluştur
cat > ~/.local/bin/hermes_durum << 'SCRIPT'
#!/bin/bash
PYTHONPATH=/home/hermes/hermes_data /opt/hermes/venv/bin/python -c "
from hermes_brain_core import run_brain_health_report
import json
print(json.dumps(run_brain_health_report(), indent=2, ensure_ascii=False))
"
SCRIPT
chmod +x ~/.local/bin/hermes_durum
```

### Alternatif: .bashrc Alias (sınırlı)

Alias'lar `.bashrc`'ye eklenebilir ama terminal aracı non-interactive shell kullandığı için sadece `bash -i -c` ile çalışır. Script yaklaşımı daha güvenilir.

```bash
# .bashrc alias (interactive shell only)
alias hermes_durum='PYTHONPATH=/home/hermes/hermes_data /opt/hermes/venv/bin/python -c "from hermes_brain_core import run_brain_health_report; import json; print(json.dumps(run_brain_health_report(), indent=2, ensure_ascii=False))"'
```

### PATH doğrulama

```bash
which hermes_durum  # → ~/.local/bin/hermes_durum yazmalı
```

## Servis Sağlığı

### Anlık Durum

```bash
hermes_durum
# veya direkt:
PYTHONPATH=/home/hermes/hermes_data /opt/hermes/venv/bin/python -c "from hermes_brain_core import run_brain_health_report; import json; print(json.dumps(run_brain_health_report(), indent=2, ensure_ascii=False))"
```

### Sağlık Raporu Bileşenleri

| Bileşen | Port | Kontrol |
|---|---|---|
| Hermes service | systemd | `systemctl is-active hermes.service` |
| Embedding Daemon | 8767 | `curl -s http://127.0.0.1:8767/health` |
| PostgreSQL | 5432 | `pg_isready -h 127.0.0.1 -p 5432` |
| tools.py import | — | `python3.11 -c "import sys; sys.path.insert(0,'/home/hermes/hermes_data'); import tools"` |
| MCP servers | 8765 | `journalctl -u hermes.service -n 80 --no-pager` |

### Embedding Daemon Watchdog

```bash
# Cron: her 5dk'da /health endpoint'ini kontrol eder
# Düşerse restart atar
curl -s http://127.0.0.1:8767/health
# → {"status": "ok", "model_loaded": true, "port": 8767, "uptime": "..."}
```

## Bileşen Emeklilik Prosedürü

Kırık/eskimiş bir servisi üretimden kaldırırken:

### 1. Fonksiyonel Alternatif Doğrula

Servisi kaldırmadan önce tüm işlevlerinin başka bir sistem tarafından karşılandığından emin ol.

### 2. Health Check'ten Kaldır

Sağlık raporu üreten fonksiyondan (`collect_runtime_health_components()`) kontrolü sil. Yoksa rapor sürekli "degraded" gösterir.

Örnek (`hermes_brain_core.py`):
```python
# SİLİNECEK:
status, detail = _http_json("http://127.0.0.1:8001/api/v2/heartbeat")
components.append({"ad": "EskiServis", "durum": status, "detay": detail})
```

### 3. Kod Yönlendirmelerini Güncelle

Eski servisi çağıran tüm fonksiyonları yeni servise yönlendir:

```python
# ESKİ: beyin_ara() → chromadb koleksiyon sorgula
# YENİ: beyin_ara() → pg_ara_vector() (PostgreSQL)
```

### 4. Sağlık Raporunu Doğrula

```bash
hermes_durum  # → "broken": [], "overall": "healthy"
```

### 5. Bağımlılıkları Temizle

```bash
pip3 uninstall eski-paket
```

## Pitfalls

- **/usr read-only** — `apt install`, `/usr/local/bin` yazma girişimleri başarısız olur. Çözüm için yukarıdaki global komut bölümüne bak.
- **Disk %95+** — `dpkg` ve `apt` çalışmaz (`dpkg: error: disk full`). Önce elle temizle.
- **Embedding modeli silme** — sadece kullanılmayan modelleri sil. Aktif modeli silersen Embedding Daemon embedding üretemez.
- **Test VM** — bu sunucu bir VPS, donanım değişikliği mümkün değil. Disk ekleme yok, sadece temizlik.
- **Alias vs Script** — terminal aracı non-interactive shell kullanır (`.bashrc` çalışmaz). Script'leri `~/.local/bin/`'e koy, alias değil.

## Related Skills

- `postgresql-memory` — PostgreSQL + pgvector entegrasyonu, Embedding Daemon detayları
