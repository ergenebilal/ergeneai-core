# 2 Haziran 2026 — Gerçek Kurulum Hikayesi

## Ortam
- Ubuntu 22.04, Hermes Agent, DeepSeek V4 Flash
- Disk: 59G toplam, 56G kullanımda (%98 dolu)
- /usr ve /etc read-only mount
- PostgreSQL yok, pgvector yok, psycopg2 yok

## Adımlar

### 1. Disk Temizliği
```bash
sudo apt-get clean                    # paket önbelleği
sudo journalctl --vacuum-time=3d      # log temizliği
rm -rf /tmp/*                         # geçici dosyalar
```
1.7GB boşaldı. PostgreSQL için yeterli.

### 2. Read-only /etc ve /usr'ı remount
```bash
sudo mount -o remount,rw /etc
sudo mount -o remount,rw /usr
```
`/etc/ld.so.cache~` yazılamadığı için dpkg hata veriyordu. Remount sonrası düzeldi.

### 3. PostgreSQL Kurulumu
```bash
sudo apt-get install -y postgresql-14 postgresql-server-dev-14
```
`libc-bin` configure hatası → `/etc` remount ile çözüldü.

### 4. pgvector Derleme
```bash
cd /tmp
git clone --depth 1 https://github.com/pgvector/pgvector.git
cd pgvector
make                    # İlk denemede postgresql-server-dev-14 eksik → hata
sudo apt-get install -y postgresql-server-dev-14  # düzeltme
make clean && make && sudo make install            # başarılı
```

### 5. Veritabanı + Tablo
```sql
CREATE DATABASE ergeneai;
CREATE USER hermes WITH PASSWORD 'hermes_2026';
CREATE EXTENSION vector;
CREATE TABLE hermes_memory (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    category VARCHAR(50),
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ON hermes_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 6. Python Kütüphanesi
```bash
pip3.11 install psycopg2-binary sentence-transformers
```

### 7. tools.py Entegrasyonu
33 satırlık eski PostgreSQL fonksiyonları → 120+ satır embedding destekli versiyona yükseltildi.

## Yaşanan Hatalar ve Çözümleri

| Hata | Sebep | Çözüm |
|---|---|---|
| `apt-get install` subprocess error 1 | Disk %98 dolu + /etc read-only | `apt-get clean` + `remount,rw /etc` |
| `unable to clean up mess surrounding ./usr/lib/postgresql` | /usr read-only | `mount -o remount,rw /usr` |
| pgvector `bitutils.o` compilation error | postgresql-server-dev-14 eksik | `apt-get install` ile kur |
| `ModuleNotFoundError: google.oauth2` | python3 kullanılıyor | `python3.11` ile çalıştır |
| `psycopg2` install fails | native extension derleme | `pip install psycopg2-binary` |
| HF Hub auth warning | `HF_TOKEN` yok | Benign, opsiyonel token |

## Test Komutları

```python
from tools import *

# Kaydet (embedding otomatik)
pg_kaydet("test bilgi", "tech_note")

# Semantik ara
pg_ara_vector("kurye birakma")

# Keyword ara
pg_ara("postgresql")

# Son kayıtlar
pg_son(5)
```

## Mevcut tools.py Fonksiyonları (53 toplam)

PostgreSQL grubu:
- `pg_baglan()` — bağlantı
- `pg_kaydet(content, category)` — embedding + kayıt
- `pg_ara(search_text, limit)` — ILIKE keyword search
- `pg_ara_vector(query, limit, threshold)` — cosine similarity search
- `pg_son(limit)` — son kayıtlar

Chromadb grubu:
- `beyin_ara(soru, n_results)` — ChromaDB semantik arama
- `beyin_kaydet(bilgi, tur, etiket)` — ChromaDB'ye kaydet
- `bilal_notes_ara(soru, n_results)` — Bilal'in notlarında ara
- `dosya_ekle(dosya_yolu, koleksiyon)` — dosyayı ChromaDB'ye ekle
