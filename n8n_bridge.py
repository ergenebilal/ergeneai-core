#!/usr/bin/env python3.11
"""
n8n Bridge v2 — Embedding Daemon baglantili
===========================================
Oncelikle yerel Embedding Daemon'a (localhost:8767) istek atar.
Daemon yoksa kendi modelini yukler (fallback).

KULLANIM (n8n Execute Command Node):
    python3.11 /home/hermes/hermes_data/n8n_bridge.py --action save --input /tmp/input.json
    python3.11 /home/hermes/hermes_data/n8n_bridge.py --action search --input /tmp/input.json

KULLANIM (CLI):
    python3.11 /home/hermes/hermes_data/n8n_bridge.py --action save --content "not" --category "genel"
    python3.11 /home/hermes/hermes_data/n8n_bridge.py --action search --query "ne dedim"
"""

import sys
import os
import json
import traceback
import urllib.request
import urllib.error

DAEMON_URL = "http://localhost:8767"
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ergeneai",
    "user": "hermes",
    "password": "hermes_2026"
}


def _daemon_istek(endpoint: str, data: dict) -> dict:
    """Embedding Daemon'a POST istek atar."""
    try:
        req = urllib.request.Request(
            f"{DAEMON_URL}{endpoint}",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.ConnectionRefusedError, urllib.error.URLError):
        return None
    except Exception as e:
        return {"hata": str(e)}


def _embed_daemon(text: str):
    """Daemon'dan embedding alir."""
    result = _daemon_istek("/embed", {"text": text})
    if result and "vector" in result:
        return result["vector"]
    return None


def _pg_baglan():
    """PostgreSQL baglantisi."""
    import psycopg2
    return psycopg2.connect(**PG_CONFIG)


def _embed_local(text: str):
    """Fallback: direkt model yukle."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        return model.encode(text).tolist()
    except Exception:
        return None


def _get_embedding(text: str):
    """Once daemon, yoksa direkt model."""
    v = _embed_daemon(text)
    if v:
        return v
    print("[BRIDGE] Daemon'a erisilemedi, direkt model yukleniyor...")
    return _embed_local(text)


def save_memory(content: str, category: str = "genel") -> str:
    """Hafizaya kaydet."""
    if not content.strip():
        return json.dumps({"hata": "Bos content"})

    # Daemon'a direkt save iste
    result = _daemon_istek("/memory/save", {"content": content, "category": category})
    if result and "sonuc" in result:
        return json.dumps(result, ensure_ascii=False)

    # Fallback: direkt PG
    embedding_vector = _get_embedding(content)
    try:
        conn = _pg_baglan()
        with conn.cursor() as cur:
            if embedding_vector:
                cur.execute(
                    "INSERT INTO hermes_memory (content, category, embedding) VALUES (%s, %s, %s)",
                    (content, category, embedding_vector)
                )
            else:
                cur.execute(
                    "INSERT INTO hermes_memory (content, category) VALUES (%s, %s)",
                    (content, category)
                )
            conn.commit()
        conn.close()
        return json.dumps({"sonuc": f"Hafizaya kaydedildi ({category})", "kategori": category})
    except Exception as e:
        return json.dumps({"hata": str(e)})


def search_memory(sorgu: str, limit: int = 5, esik: float = 0.3) -> str:
    """Vektor arama."""
    if not sorgu.strip():
        return json.dumps({"hata": "Bos sorgu"})

    # Daemon'a direkt search iste
    result = _daemon_istek("/memory/search", {"sorgu": sorgu, "limit": limit, "esik": esik})
    if result and "sonuc" in result:
        return json.dumps(result["sonuc"], ensure_ascii=False)

    # Fallback: direkt PG
    embedding_vector = _get_embedding(sorgu)
    if not embedding_vector:
        return json.dumps({"hata": "Embedding alinamadi"})
    try:
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
                    "id": r[0], "content": r[1][:500],
                    "category": r[2], "benzerlik": round(r[3], 3),
                    "tarih": str(r[4])[:10]
                })
        conn.close()
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"hata": str(e)})


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True, choices=["save", "search"])
    parser.add_argument("--input", help="JSON dosyasi")
    parser.add_argument("--content", help="Kayit icerigi (save)")
    parser.add_argument("--category", default=None, help="Kategori (save)")
    parser.add_argument("--query", help="Arama sorgusu (search)")
    parser.add_argument("--limit", type=int, default=5, help="Sonuc sayisi")
    parser.add_argument("--esik", type=float, default=0.3, help="Benzerlik esigi")
    args = parser.parse_args()

    # Input dosyasindan oku
    data = {}
    if args.input:
        with open(args.input, "r") as f:
            data = json.load(f)

    if args.action == "save":
        content = args.content or data.get("content", "")
        category = args.category or data.get("category", "genel")
        print(save_memory(content, category))
    elif args.action == "search":
        sorgu = args.query or data.get("sorgu", "")
        limit = args.limit if args.limit != 5 else data.get("limit", 5)
        esik = args.esik if args.esik != 0.3 else data.get("esik", 0.3)
        print(search_memory(sorgu, limit, esik))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"hata": f"Bridge hatasi: {str(e)}"}))
        sys.exit(1)
