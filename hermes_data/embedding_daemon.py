#!/usr/bin/env python3.11
"""
Embedding Daemon — Hermes Hafiza Motoru API Sunucusu
====================================================
- sentence-transformers modelini RAM'de sıcak tutar (0 ms gecikme)
- PostgreSQL'e vektörlü kayıt/arama yapar
- n8n HTTP Request node ile direkt çağrılır (dosya paylaşımı GEREKMEZ)
- Port: 8767 (MCP 8765, Nanobot 8766'nın yanı)

KULLANIM:
    python3.11 embedding_daemon.py
    # Arka planda: nohup python3.11 embedding_daemon.py > ~/embedding_daemon.log 2>&1 &

ENDPOINT'LER:
    POST /embed          {"text": "..."}              → {"vector": [0.1, ...]}
    POST /memory/save    {"content": "...", "category": "..."}  → {"sonuc": "..."}
    POST /memory/search  {"sorgu": "...", "limit": 5}  → [...]
    GET  /health                                        → {"status": "ok", ...}
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# === PostgreSQL ===
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ergeneai",
    "user": "hermes",
    "password": "hermes_2026"
}

import psycopg2

# === Embedding Model (RAM'de sıcak) ===
_model = None

def _get_model():
    global _model
    if _model is None:
        print("[DAEMON] Model yukleniyor...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        print(f"[DAEMON] Model hazir! (384 boyut)")
    return _model


def _pg_baglan():
    return psycopg2.connect(**PG_CONFIG)


class EmbeddingAPI(BaseHTTPRequestHandler):
    """HTTP API handler — embedding + hafiza islemleri."""

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"text": raw.decode("utf-8").strip()}

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            self._send_json({
                "status": "ok",
                "model_loaded": _model is not None,
                "port": 8767,
                "uptime": f"{time.time() - start_time:.0f}s"
            })
        else:
            self._send_json({"hata": f"Bilinmeyen endpoint: {path}"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_body()

        try:
            if path == "/embed":
                result = self._handle_embed(data)
            elif path == "/memory/save":
                result = self._handle_save(data)
            elif path == "/memory/search":
                result = self._handle_search(data)
            else:
                result = {"hata": f"Bilinmeyen endpoint: {path}"}
                self._send_json(result, 404)
                return
            self._send_json(result)
        except Exception as e:
            self._send_json({"hata": str(e)}, 500)

    def _handle_embed(self, data):
        text = data.get("text", "")
        if not text.strip():
            return {"hata": "Bos metin gonderilemez"}
        model = _get_model()
        vector = model.encode(text).tolist()
        return {
            "vector": vector,
            "boyut": len(vector),
            "metin_kesiti": text[:100]
        }

    def _handle_save(self, data):
        content = data.get("content", "").strip()
        category = data.get("category", "genel")
        if not content:
            return {"hata": "Bos content gonderilemez"}

        model = _get_model()
        embedding_vector = model.encode(content).tolist()
        conn = _pg_baglan()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO hermes_memory (content, category, embedding) VALUES (%s, %s, %s)",
                (content, category, embedding_vector)
            )
            conn.commit()
        conn.close()
        return {"sonuc": f"✅ Hafizaya kaydedildi ({category})", "kategori": category}

    def _handle_search(self, data):
        sorgu = data.get("sorgu", "").strip()
        limit = int(data.get("limit", 5))
        esik = float(data.get("esik", 0.3))
        if not sorgu:
            return {"hata": "Bos sorgu gonderilemez"}

        model = _get_model()
        embedding_vector = model.encode(sorgu).tolist()
        conn = _pg_baglan()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content, category, "
                "1 - (embedding <=> %s::vector) AS benzerlik, "
                "created_at FROM hermes_memory "
                "WHERE embedding IS NOT NULL "
                "AND 1 - (embedding <=> %s::vector) > %s "
                "ORDER BY benzerlik DESC LIMIT %s",
                (embedding_vector, embedding_vector, esik, limit)
            )
            results = []
            for r in cur.fetchall():
                results.append({
                    "id": r[0],
                    "content": r[1][:500],
                    "category": r[2],
                    "benzerlik": round(r[3], 3),
                    "tarih": str(r[4])[:10]
                })
        conn.close()
        return {"sonuc": results, "adet": len(results)}


def main():
    global start_time
    start_time = time.time()

    port = 8767
    host = "0.0.0.0"

    print(f"╔══════════════════════════════════╗")
    print(f"║   HERMES EMBEDDING DAEMON v1.0   ║")
    print(f"╚══════════════════════════════════╝")
    print(f"[DAEMON] Port: {port}")
    print(f"[DAEMON] Model: paraphrase-multilingual-MiniLM-L12-v2")
    print(f"[DAEMON] PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['dbname']}")

    # Model'i baslangicta yukle
    print("[DAEMON] Model ön yükleme yapiliyor...")
    t0 = time.time()
    _get_model()
    print(f"[DAEMON] Model ön yükleme tamam ({time.time()-t0:.1f}s)")

    # PostgreSQL baglanti testi
    try:
        conn = _pg_baglan()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM hermes_memory")
            count = cur.fetchone()[0]
        conn.close()
        print(f"[DAEMON] PostgreSQL baglandi. Hafizada {count} kayit.")
    except Exception as e:
        print(f"[DAEMON] ⚠️ PostgreSQL baglanti hatasi: {e}")

    print(f"[DAEMON] Sunucu baslatiliyor: http://{host}:{port}")
    print(f"[DAEMON]   POST /embed          → vektor")
    print(f"[DAEMON]   POST /memory/save     → hafizaya kayit")
    print(f"[DAEMON]   POST /memory/search   → vektor arama")
    print(f"[DAEMON]   GET  /health          → durum kontrolü")

    server = HTTPServer((host, port), EmbeddingAPI)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[DAEMON] Kapatiliyor...")
        server.server_close()


if __name__ == "__main__":
    main()
