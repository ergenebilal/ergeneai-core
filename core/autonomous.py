"""
Autonomous orchestrator module.
Handles autonomous task execution: search ChromaDB, verify with LongTracer, return results.
"""
from .chroma_store import search_notes
from .ai_tools import verify_claim
from .system_utils import get_now


def run_autonomous(goal: str) -> dict:
    """Searches the goal directly in ChromaDB and verifies results with LongTracer.

    Args:
        goal: The search goal/task description

    Returns:
        dict: {'search_result': [...], 'verification': {...}}
    """
    try:
        now = get_now()
        print(f"Current: {now['date']} {now['time']}, {now['day']}")

        # 1. Search in ChromaDB
        search_result = search_notes(goal)
        if not search_result:
            return {"search_result": [], "verification": "No results in ChromaDB"}

        # 2. Take the first (most relevant) result
        first_result = search_result[0]

        # 3. Verify with source
        verification = verify_claim(first_result, "ChromaDB record")

        return {
            "search_result": search_result,
            "verification": verification
        }
    except Exception as e:
        return {"error": str(e)}
