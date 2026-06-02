#!/usr/bin/env python3.11
"""
n8n Bridge — Hermes Hafiza Motoru icin bagimsiz Python gecidi.

tools.py'ye bagimli DEGILDIR. Kendi psycopg2 ve embedding baglantisi vardir.
Bu sayede n8n Execute Command Node'u hangi Python'u kullanirsa kullansin calisir.

KULLANIM (n8n Execute Command Node'undan):
    python3 /home/hermes/hermes_data/n8n_bridge.py --action save_memory --input /tmp/n8n_input.json

N8N INPUT DOSYASI ORNEGI (/tmp/n8n_input.json):
    {"content": "...", "category": "business_strategy"}
    veya
    {"sorgu": "vektor arama metni", "limit": 5, "esik": 0.3}

CIKTI: stdout'a JSON basar, n8n bunu yakalar.
"""

import sys
import os
import json
import traceback

# === PostgreSQL Baglantisi ===
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ergeneai",
    "user": "hermes",
    "password": "hermes_2026"
}

def _pg_baglan():
    """PostgreSQL baglantisi acar."""
    import psycopg2
    return psycopg2.connect(**PG_CONFIG)


def _get_embedding(text: str):
    """Metni 384 boyutlu vektore donusturur."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        return model.encode(text).tolist()
    except Exception as e:
        return None


def save_memory(data: dict) -> str:
    """Hafizaya kayit."""
    content = data.get("content", "").strip()
    category = data.get("category", "genel")
    if not content:
        return json.dumps({"hata": "Bos content gonderilemez"})

    try:
        embedding_vector = _get_embedding(content)
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
        return json.dumps({"sonuc": f"✅ PG beyne kaydedildi ({category})", "kategori": category})
    except Exception as e:
        return json.dumps({"hata": f"PG kayit hatasi: {str(e)}"})


def search_memory(data: dict) -> str:
    """Vektorel (semantik) arama."""
    sorgu = data.get("sorgu", "").strip()
    limit = data.get("limit", 5)
    esik = data.get("esik", 0.3)
    if not sorgu:
        return json.dumps({"hata": "Bos sorgu gonderilemez"})

    try:
        embedding_vector = _get_embedding(sorgu)
        if not embedding_vector:
            return json.dumps({"hata": "Embedding modeli yuklu degil, vektor aramasi yapilamadi"})

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
                    "content": r[1][:300],
                    "category": r[2],
                    "benzerlik": round(r[3], 3),
                    "tarih": str(r[4])[:10]
                })
        conn.close()
        return json.dumps(results if results else [], ensure_ascii=False)
    except Exception as e:
        return json.dumps({"hata": f"Vektor arama hatasi: {str(e)}"})


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"hata": "Kullanim: --action [save_memory|search_memory] --input /tmp/dosya.json"}))
        sys.exit(1)

    action = None
    input_path = None
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--action" and i + 1 < len(sys.argv[1:]):
            action = sys.argv[i + 2]
        elif arg == "--input" and i + 1 < len(sys.argv[1:]):
            input_path = sys.argv[i + 2]

    if not action or not input_path:
        print(json.dumps({"hata": "--action ve --input zorunludur"}))
        sys.exit(1)

    if not os.path.exists(input_path):
        print(json.dumps({"hata": f"Input dosyasi bulunamadi: {input_path}"}))
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        with open(input_path, "r", encoding="utf-8") as f:
            raw = f.read()
        data = {"content": raw, "category": "genel", "sorgu": raw}

    if action == "save_memory":
        output = save_memory(data)
    elif action == "search_memory":
        output = search_memory(data)
    else:
        output = json.dumps({"hata": f"Bilinmeyen aksiyon: {action}"})

    print(output)

    # Temp dosyayi temizle
    try:
        os.remove(input_path)
    except:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
            "hata": f"Bridge hatasi: {str(e)}",
            "trace": traceback.format_exc()
        }))
        sys.exit(1)
