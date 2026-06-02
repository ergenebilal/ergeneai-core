# n8n_bridge.py — Kullanım Referansı

## Nedir
n8n ile Embedding Daemon arasında CLI köprüsü. Daemon'a istek atar, yoksa fallback olarak direkt PostgreSQL'e yazar.

## Path
`/home/hermes/hermes_data/n8n_bridge.py`

## Kullanım

```bash
# Hafızaya kaydet
python3.11 /home/hermes/hermes_data/n8n_bridge.py --save "içerik" "kategori"

# Vektör ara
python3.11 /home/hermes/hermes_data/n8n_bridge.py --search "sorgu" 5

# JSON dosyasından oku
python3.11 /home/hermes/hermes_data/n8n_bridge.py --action save --input /tmp/input.json
```

## Önemli
- `python3.11` ile çalıştır (psycopg2 + sentence-transformers bu sürümde)
- Daemon (8767) çalışıyorsa → 20ms'de yanıt
- Daemon yoksa → model yüklenir (~2sn), sonra yazma
- Standalone'dır, tools.py'ye bağımlı DEĞİLDİR
- Daemon'a tercih sebebi: n8n container izolasyonu
