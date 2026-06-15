"""
PostgreSQL memory (second brain) module.
Handles vector-augmented memory storage, semantic search, and proactive analysis.
"""
import datetime

import psycopg2


# === CONFIGURATION ===
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ergeneai",
    "user": "hermes",
    "password": "hermes_2026"
}

# Embedding model (cached singleton)
_embedding_model = None


def _get_embedding_model():
    """Loads the SentenceTransformer model as a singleton."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            print(f"⚠️ Embedding model could not be loaded: {e}")
            _embedding_model = None
    return _embedding_model


def _get_embedding(text: str) -> list:
    """Converts text to a 384-dimensional vector (local model, free).

    Args:
        text: Input text

    Returns:
        list: Embedding vector or None
    """
    model = _get_embedding_model()
    if model:
        return model.encode(text).tolist()
    return None


def get_pg_connection():
    """Opens a PostgreSQL database connection.

    Returns:
        connection: psycopg2 connection object
    """
    return psycopg2.connect(**PG_CONFIG)


def save_memory_pg(content: str, category: str = "genel") -> str:
    """Saves text with its vector embedding to PostgreSQL memory.

    Args:
        content: Information to save
        category: Category (tech_note, business_strategy, personal_reminder, genel)

    Returns:
        str: Operation result
    """
    try:
        embedding_vector = _get_embedding(content)
        conn = get_pg_connection()
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
        return f"✅ Saved to PG brain ({category})"
    except Exception as e:
        return f"❌ PG save error: {str(e)}"


def search_memory_pg(search_text: str, limit: int = 5) -> list:
    """Performs text-based search in Hermes' secondary brain (PostgreSQL).

    Args:
        search_text: Text to search for
        limit: Number of results

    Returns:
        list: Matching records
    """
    try:
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content, category, created_at FROM hermes_memory "
                "WHERE content ILIKE %s ORDER BY created_at DESC LIMIT %s",
                (f"%{search_text}%", limit)
            )
            results = [{"id": r[0], "content": r[1][:300], "category": r[2], "date": str(r[3])[:10]} for r in cur.fetchall()]
        conn.close()
        return results if results else ["No matches found in PG brain"]
    except Exception as e:
        return [f"PG search error: {str(e)}"]


def search_memory_vector(query: str, limit: int = 5, threshold: float = 0.3) -> list:
    """Performs semantic vector search using cosine similarity in PostgreSQL.

    An alternative to ChromaDB, more scalable for large datasets.

    Args:
        query: Search text (natural language)
        limit: Number of results
        threshold: Similarity threshold (0.0-1.0, higher = more similar)

    Returns:
        list: List of dicts with id, content, category, similarity, date
    """
    try:
        embedding_vector = _get_embedding(query)
        if not embedding_vector:
            return ["⚠️ Embedding model not loaded, falling back to text search..."] + search_memory_pg(query, limit)

        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content, category, "
                "1 - (embedding <=> %s::vector) AS similarity, "
                "created_at FROM hermes_memory "
                "WHERE embedding IS NOT NULL "
                "AND 1 - (embedding <=> %s::vector) > %s "
                "ORDER BY similarity DESC LIMIT %s",
                (embedding_vector, embedding_vector, threshold, limit)
            )
            results = []
            for r in cur.fetchall():
                results.append({
                    "id": r[0],
                    "content": r[1][:300],
                    "category": r[2],
                    "similarity": round(r[3], 3),
                    "date": str(r[4])[:10]
                })
        conn.close()
        return results if results else ["No matches found in vector search"]
    except Exception as e:
        return [f"PG vector search error: {str(e)}"]


def get_recent_memories(limit: int = 5) -> list:
    """Returns the most recently added records.

    Args:
        limit: Number of records

    Returns:
        list: Recent records
    """
    try:
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content, category, created_at FROM hermes_memory "
                "ORDER BY created_at DESC LIMIT %s", (limit,)
            )
            results = [{"id": r[0], "content": r[1][:200], "category": r[2], "date": str(r[3])[:10]} for r in cur.fetchall()]
        conn.close()
        return results
    except Exception as e:
        return [f"PG query error: {str(e)}"]


def run_proactive_analysis() -> dict:
    """Analyzes PG memory for the proactive morning briefing.

    Fetches tech_note and business_strategy records from the last 48 hours,
    analyzes them with Ollama (qwen2.5:3b), and generates a 3-section summary.

    Returns:
        dict: Summary with 'summary' and 'record_count' keys
    """
    try:
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content, category, created_at FROM hermes_memory "
                "WHERE category IN ('tech_note', 'business_strategy') "
                "AND created_at > NOW() - INTERVAL '48 hours' "
                "ORDER BY created_at DESC"
            )
            records = cur.fetchall()
        conn.close()

        if not records:
            return {"summary": "No strategic records found in the last 48 hours.", "record_count": 0}

        record_text = "\n".join([f"[{r[1]}] {str(r[2])[:10]}: {r[0][:300]}" for r in records])

        import ollama
        prompt = f"""You are Hermes proactive analysis engine. Analyze the notes recorded in the last 48 hours below and produce a 3-section summary in TURKISH:

1. TODAY'S FOCUS POINT (1-2 most critical items)
2. OPPORTUNITIES (inputs that can be turned into leverage)
3. OPERATIONAL RISKS (threats requiring action)

NOTES:
{record_text}

RESPONSE FORMAT (TURKISH):
**Gunun Odak Noktasi**
- ...

**Firsatlar**
- ...

**Operasyonel Riskler**
- ..."""

        response = ollama.chat(
            model='qwen2.5:3b',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.3, 'num_predict': 500}
        )

        return {"summary": response['message']['content'].strip(), "record_count": len(records)}
    except Exception as e:
        return {"summary": f"Analysis error: {str(e)}", "record_count": 0, "error": str(e)}
