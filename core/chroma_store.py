"""
ChromaDB operations module.
Handles vector store search, file indexing, and brain (persistent memory) operations.
"""
import os
import hashlib
import datetime
import chromadb
from chromadb.utils import embedding_functions


# === CONFIGURATION ===
CHROMA_HOST = "localhost"
CHROMA_PORT = 8001


def search_notes(query: str, n_results: int = 3) -> list:
    """Searches the 'bilal_notes' collection in ChromaDB.

    Args:
        query: Search query text
        n_results: Number of results to return (default: 3)

    Returns:
        list: Found documents list
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection("bilal_notes")
        results = collection.query(query_texts=[query], n_results=n_results)
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        return [f"Search error: {str(e)}"]


def add_file_to_chroma(file_path: str, collection_name: str = "bilal_notes") -> str:
    """Adds a file to a ChromaDB collection.

    Args:
        file_path: Path to the file to add
        collection_name: Target collection name (default: bilal_notes)

    Returns:
        str: Operation result message
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection(collection_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        doc_id = os.path.basename(file_path)
        collection.add(documents=[content], ids=[doc_id])
        return f"✅ {doc_id} added."
    except Exception as e:
        return f"❌ File add error: {str(e)}"


def search_brain(query: str, n_results: int = 5) -> list:
    """Searches Hermes' persistent brain (ChromaDB 'hermes_beyin' collection).

    Args:
        query: Search query
        n_results: Number of results

    Returns:
        list: Found documents
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection("hermes_beyin")
        results = collection.query(query_texts=[query], n_results=n_results)
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        # Create collection if it does not exist
        if "does not exist" in str(e):
            return ["🧠 Hermes brain not yet created. Initialize with 'save_to_brain'."]
        return [f"Brain error: {str(e)}"]


def save_to_brain(info: str, kind: str = "genel", tag: str = "") -> str:
    """Saves information to Hermes' persistent brain (ChromaDB).

    Args:
        info: Information text to save
        kind: Information type (genel, soz, hedef, ogrenme, hata)
        tag: Optional tag

    Returns:
        str: Operation result
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        try:
            collection = client.get_collection("hermes_beyin")
        except Exception:
            collection = client.create_collection(
                name="hermes_beyin",
                embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name='paraphrase-multilingual-MiniLM-L12-v2'
                )
            )

        doc_id = hashlib.md5(info.encode()).hexdigest()[:16]

        collection.add(
            documents=[info],
            ids=[doc_id],
            metadatas=[{"tur": kind, "etiket": tag, "tarih": datetime.datetime.now().isoformat()[:10]}]
        )
        return f"✅ Saved to brain ({kind})"
    except Exception as e:
        return f"❌ Brain save error: {str(e)}"
