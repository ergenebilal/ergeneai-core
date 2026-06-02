# PostgreSQL + pgvector İkinci Beyin

## Kurulum (2 Haziran 2026)

- PostgreSQL 14 kuruldu (apt install postgresql-14 postgresql-server-dev-14)
- pgvector source'dan build edildi (git clone → make → make install)
- `/usr` ve `/etc` read-only idi → `sudo mount -o remount,rw /etc /usr` ile fix

## Veritabanı

```sql
CREATE DATABASE ergeneai;
CREATE USER hermes WITH PASSWORD 'hermes_2026';
GRANT ALL PRIVILEGES ON DATABASE ergeneai TO hermes;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE hermes_memory (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    category VARCHAR(50),          -- tech_note, business_strategy, personal_reminder, genel
    embedding VECTOR(1536),         -- OpenAI/DeepSeek vektör boyutu
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON hermes_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## tools.py Fonksiyonları

```python
pg_baglan()     → psycopg2.connect(**PG_CONFIG)
pg_kaydet()     → INSERT INTO hermes_memory (content, category)
pg_ara()        → SELECT ... WHERE content ILIKE '%search%'
pg_son()        → SELECT ... ORDER BY created_at DESC
```

## Durum

- ILIKE text search çalışıyor ✅
- pgvector index hazır, embedding doldurulmayı bekliyor
- 3 kategori aktif: tech_note, business_strategy, personal_reminder

## Embedding Ekleneceği Zaman

```python
# OpenAI embedding
import openai
resp = openai.embeddings.create(model="text-embedding-3-small", input="metin")
vec = resp.data[0].embedding  # 1536 boyut

# DeepSeek embedding  
# (DeepSeek embedding endpoint kullanılacaksa)

# PostgreSQL'e embedding'li kaydet
cur.execute(
    "INSERT INTO hermes_memory (content, category, embedding) VALUES (%s, %s, %s)",
    (content, category, vec)
)

# Vektör arama
cur.execute(
    "SELECT content, category, 1 - (embedding <=> %s::vector) AS similarity "
    "FROM hermes_memory WHERE embedding IS NOT NULL "
    "ORDER BY similarity DESC LIMIT 5", (query_vec,)
)
```
