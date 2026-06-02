#!/usr/bin/env python3
"""
n8n Bridge — Hermes Hafiza Motoru icin guvenli Python gecidi.

KULLANIM (n8n Execute Command Node'undan):
    python3 /home/hermes/hermes_data/n8n_bridge.py --action save_memory --input /tmp/n8n_input.json

N8N INPUT DOSYASI ORNEGI (/tmp/n8n_input.json):
    {
        "content": "Melike Hanim ile toplanti...",
        "category": "business_strategy",
        "sorgu": "vektor arama metni"
    }

CIKTI: stdout'a JSON array/string basar, n8n bunu yakalar.
"""

import sys
import os
import json
import traceback

# tools.py'yi import et (ana dizin)
sys.path.insert(0, os.path.expanduser("~/hermes_data"))
import tools


def save_memory(data: dict) -> str:
    """Hafızaya kayıt."""
    content = data.get("content", "")
    category = data.get("category", "genel")
    if not content.strip():
        return json.dumps({"hata": "Bos content gonderilemez"})
    result = tools.pg_kaydet(content, category)
    return json.dumps({"sonuc": result, "kategori": category})


def search_memory(data: dict) -> str:
    """Vektorel arama."""
    sorgu = data.get("sorgu", "")
    limit = data.get("limit", 5)
    esik = data.get("esik", 0.3)
    if not sorgu.strip():
        return json.dumps({"hata": "Bos sorgu gonderilemez"})
    results = tools.pg_ara_vector(sorgu, limit=limit, esik=esik)
    return json.dumps(results, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"hata": "Kullanim: --action [save_memory|search_memory] --input /tmp/dosya.json"}))
        sys.exit(1)

    # Argumanlari parse et
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

    # Input dosyasini oku
    if not os.path.exists(input_path):
        print(json.dumps({"hata": f"Input dosyasi bulunamadi: {input_path}"}))
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        # JSON degilse duz metin oku
        with open(input_path, "r", encoding="utf-8") as f:
            raw = f.read()
        data = {"content": raw, "category": "genel", "sorgu": raw}

    # Aksiyona gore yonlendir
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
