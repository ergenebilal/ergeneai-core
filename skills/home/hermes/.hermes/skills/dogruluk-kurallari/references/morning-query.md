# Sabah Raporu (morning_query.py)

## Ne işe yarar

Auto-feed pipeline'ının tamamlayıcısı. Feed toplandıktan sonra ChromaDB'de ne var diye bakar, son feed'leri ve hata durumunu özetler.

## Kullanım

```bash
python3.11 ~/hermes_data/morning_query.py
# veya
python3.11 ~/.hermes/skills/dogruluk-kurallari/scripts/morning_query.py
```

## Çıktı Örneği

```text
=== HERMES SABAH RAPORU ===
📚 Yeni eklenen bilgiler: 6 doküman
⚠️  Son hatalar: 0 kayıt
✅ Sistem hazır.
```

## Bilinen Sorun

`morning_query.py` → `tools.py` → `bilal_notes_ara()` → `chromadb.HttpClient()` → embedding model generation. `bilal_notes` koleksiyonu `paraphrase-multilingual-MiniLM-L12-v2` embedding modeli kullandığı için `sentence-transformers` kurulu değilse `collection.query()` patlar. Ayrıca `calendar.py` shadowing de import'ı bozabilir.

**Geçici çözüm:** ChromaDB REST API ile direkt sorgula (bkz. `references/chromadb-rest-api.md`) — curl ile `/api/v2/tenants/default_tenant/databases/default_database/collections/{id}/get` endpoint'ine POST yap, doküman sayısını al.

## Cron'a bağlama

Şu an `morning_query.py` cron'da değil. Auto-feed (`auto-feed-daily`) çalıştığında ChromaDB'ye kaydeder ve direkt Telegram'a bildirim atar. Ayrı bir sabah raporu cron job'ı gereksiz.

Detay: `references/auto-feed-pipeline.md`

## İlişkili Dosyalar

- `~/hermes_data/morning_query.py` — Ana script
- `~/hermes_data/auto_feed.py` — Feed toplama script'i
- `references/auto-feed-pipeline.md` — Feed pipeline dökümantasyonu
