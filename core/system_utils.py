"""
System utilities module.
Handles error logging, session memory, terminal commands, web fetching, system repair,
time/date, weather, and budget calculations.
"""
import os
import time
import subprocess
import datetime


# === CONFIGURATION ===
HATA_LOG = os.path.expanduser("~/hermes_hata_log.txt")

# === JARVIS-LEVEL ABILITIES ===
_session_memory = []


def check_system_status(service_name: str) -> dict:
    """Checks whether a system service is running.

    Args:
        service_name: Service name to check ("chroma", "docker")

    Returns:
        dict: {"status": "running"|"not_running", ...}
    """
    if service_name == "chroma":
        try:
            out = subprocess.check_output(["curl", "-sf", "http://localhost:8001/api/v2/heartbeat"], timeout=3, stderr=subprocess.DEVNULL).decode()
            return {"status": "running", "output": out} if out else {"status": "not_running"}
        except Exception:
            return {"status": "not_running", "error": "No connection"}
    elif service_name == "docker":
        try:
            subprocess.check_output(["docker", "ps"], stderr=subprocess.DEVNULL)
            return {"status": "running"}
        except Exception:
            return {"status": "not_running"}
    return {"status": "unknown", "message": f"Unknown service: {service_name}"}


def log_error(error_type: str, detail: str, correct_behavior: str) -> str:
    """Appends a new error record to the error log file.

    Args:
        error_type: Error category (e.g. "self_evolve", "chroma", "network")
        detail: Detailed error description
        correct_behavior: Correct behavior or suggested fix

    Returns:
        str: Operation result message
    """
    try:
        with open(HATA_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | ERROR: {error_type} | DETAIL: {detail} | CORRECT: {correct_behavior}\n")
        return f"✅ Error logged: {error_type}"
    except Exception as e:
        return f"❌ Could not log error: {str(e)}"


def get_error_history(limit: int = 5) -> list:
    """Returns the last N error records.

    Args:
        limit: Number of records to fetch (default: 5)

    Returns:
        list: Error records list
    """
    try:
        if not os.path.exists(HATA_LOG):
            return []
        with open(HATA_LOG, "r", encoding="utf-8") as f:
            return f.readlines()[-limit:]
    except Exception as e:
        return [f"Could not read errors: {str(e)}"]


def get_plan(goal: str) -> dict:
    """Returns plan steps based on the given goal.

    Args:
        goal: Description of the task to accomplish

    Returns:
        dict: {"steps": [...], "description": "..."}
    """
    plans = {
        "araştır": {
            "steps": ["search_notes(goal)", "verify_claim(result, source)"],
            "description": "Search in ChromaDB, then verify"
        },
        "kurulum": {
            "steps": ["check_system_status(service)", "add_file_to_chroma(file)", "log_error(...)"],
            "description": "Check system status, add file, log errors"
        },
        "rapor": {
            "steps": ["get_error_history()", "search_notes(...)"],
            "description": "Get error history, search ChromaDB"
        },
        "kod": {
            "steps": ["run_terminal('python3 code.py')", "verify_claim(...)"],
            "description": "Run code, verify result"
        },
        "web": {
            "steps": ["fetch_webpage(url)", "search_notes(...)", "add_file_to_chroma(...)"],
            "description": "Fetch data from web, search, save"
        }
    }
    for key, plan in plans.items():
        if key in goal.lower():
            return plan
    return {"steps": ["search_notes(goal)", "verify_claim(result, source)"], "description": "General research"}


def remember_session(message: str) -> list:
    """Adds a message to session memory and returns the last 5 messages.

    Args:
        message: Message to record

    Returns:
        list: Last 5 messages
    """
    try:
        _session_memory.append(message)
        return _session_memory[-5:]
    except Exception as e:
        return [f"Error: {str(e)}"]


def get_session() -> list:
    """Returns the entire session memory.

    Returns:
        list: All session messages
    """
    try:
        return _session_memory
    except Exception as e:
        return [f"Error: {str(e)}"]


def run_terminal(command: str, timeout: int = 30) -> str:
    """Runs a shell command and returns its output.

    Args:
        command: Command to execute
        timeout: Maximum wait time in seconds (default: 30)

    Returns:
        str: Command output or error message
    """
    try:
        result = subprocess.check_output(command.split(), text=True, stderr=subprocess.STDOUT, timeout=timeout)
        return result.strip()
    except subprocess.TimeoutExpired:
        return f"ERROR: Command did not complete in {timeout} seconds"
    except Exception as e:
        return f"ERROR: {str(e)}"


def fetch_webpage(url: str, max_chars: int = 2000) -> str:
    """Fetches the content of a web page via HTTP.

    Args:
        url: URL of the web page
        max_chars: Maximum number of characters (default: 2000)

    Returns:
        str: Page content or error message
    """
    try:
        import requests
        r = requests.get(url, timeout=10, headers={"User-Agent": "Hermes-Agent"})
        r.raise_for_status()
        return r.text[:max_chars]
    except Exception as e:
        return f"❌ Web error: {str(e)}"


def suggest_fix(error_message: str, attempt: int = 1) -> str:
    """Suggests a fix based on the error message.

    Args:
        error_message: The error message received
        attempt: Current attempt number (default: 1)

    Returns:
        str: Fix suggestion
    """
    try:
        if attempt >= 3:
            return "⚠️ Maximum attempts (3) exceeded. Manual intervention required."
        error = error_message.lower()
        if "chromadb" in error or "chroma" in error:
            return "🔄 Restarting ChromaDB: chroma run --host 0.0.0.0 --port 8001 &"
        elif "dosya" in error and "yok" in error:
            return "📄 Creating file: touch new_file.txt"
        elif "bağlantı" in error or "connection" in error:
            return "🌐 Checking connection: curl -I https://httpbin.org"
        else:
            return f"🛠 Unknown error, trying alternative (attempt {attempt + 1}): {error_message[:100]}"
    except Exception as e:
        return f"❌ suggest_fix error: {str(e)}"


def get_now() -> dict:
    """Returns the current date, time, and day information.

    Returns:
        dict: {"date": "2026-06-02", "time": "03:47", "day": "Tuesday", "timestamp": "2026-06-02T03:47:00"}
    """
    try:
        now = datetime.datetime.now()
        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "day": now.strftime("%A"),
            "timestamp": now.isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


def get_weather(city: str = "Bursa") -> str:
    """Queries the weather for a specified city.

    Args:
        city: City name (default: Bursa)

    Returns:
        str: Weather information or error message
    """
    try:
        import requests as req
        url = f"https://wttr.in/{city}?format=%C+%t+%h+%w&lang=tr"
        resp = req.get(url, timeout=10)
        if resp.status_code == 200:
            info = resp.text.strip()
            return f"🌤 {city}: {info}"
        return f"❌ Weather info unavailable (HTTP {resp.status_code})"
    except Exception as e:
        return f"❌ Weather error: {str(e)}"


def calculate_budget(transaction_type: str, amount: float, days_left: int) -> str:
    """Simple budget calculation: income/expense daily allocation.

    Args:
        transaction_type: "gelir" (income) or "gider" (expense)
        amount: Total amount in TL
        days_left: Days remaining

    Returns:
        str: Budget calculation result
    """
    if transaction_type == "gider":
        daily = amount / days_left if days_left > 0 else 0
        return f"Expense: {amount} TL, {days_left} days left. ~{daily:.2f} TL/day to allocate."
    elif transaction_type == "gelir":
        daily = amount / days_left if days_left > 0 else 0
        return f"Income: {amount} TL, {days_left} days left. ~{daily:.2f} TL/day will accumulate."
    else:
        return "Unknown transaction type"
