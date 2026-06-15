"""
core.db — Shared PostgreSQL config, connection, and query helpers
=================================================================
Birlesik PG_CONFIG, get_pg_connection(), SEARCH_SQL, ve
format_search_result() — n8n_bridge ve embedding_daemon arasinda
kod tekrarini onlemek icin bu modulde toplanmistir.
"""

import sys
import os

# === PostgreSQL Konfigurasyonu (tek kaynak) ===
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ergeneai",
    "user": "hermes",
    "password": "hermes_2026",
}

# === Vektor Arama Sorgusu (tek kaynak) ===
SEARCH_SQL = """
    SELECT id, content, category,
           1 - (embedding <=> %s::vector) AS benzerlik,
           created_at
    FROM hermes_memory
    WHERE embedding IS NOT NULL
      AND 1 - (embedding <=> %s::vector) > %s
    ORDER BY benzerlik DESC
    LIMIT %s
"""


def get_pg_connection():
    """
    PostgreSQL baglantisi olusturur.
    
    Returns:
        psycopg2.connection
        
    Raises:
        ImportError: psycopg2 yoksa
        psycopg2.OperationalError: baglanti hatasi
    """
    import psycopg2
    return psycopg2.connect(**PG_CONFIG)


def format_search_result(row) -> dict:
    """
    SQL sorgusundan gelen bir satiri dict'e donusturur.
    
    Args:
        row: tuple (id, content, category, benzerlik, created_at)
    
    Returns:
        dict: {"id": ..., "content": ..., "category": ..., "benzerlik": ..., "tarih": ...}
    """
    return {
        "id": row[0],
        "content": row[1][:500] if row[1] else "",
        "category": row[2],
        "benzerlik": round(row[3], 3) if row[3] is not None else 0.0,
        "tarih": str(row[4])[:10] if row[4] else "",
    }


def ensure_core_importable():
    """
    core paketinin import edilebilir oldugundan emin olur.
    Eger /opt/data/ergeneai-core Python path'inde degilse ekler.
    Bu fonksiyon dogrudan calistirilan script'ler (n8n_bridge, embedding_daemon)
    tarafindan cagrilir.
    """
    core_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if core_parent not in sys.path:
        sys.path.insert(0, core_parent)
