"""
ErgeneAI Core: Modular tools package.
Replaces the monolithic tools.py with organized, English-named modules.
"""
from .google_api import (
    authenticate,
    get_auth_url,
    send_email,
    read_emails,
    add_calendar_event,
    list_calendar_events,
    list_drive_files,
    upload_drive_file,
    read_sheet,
    write_sheet,
    append_sheet,
)

from .chroma_store import (
    CHROMA_HOST,
    CHROMA_PORT,
    search_notes,
    add_file_to_chroma,
    search_brain,
    save_to_brain,
)

from .pg_brain import (
    PG_CONFIG,
    get_pg_connection,
    save_memory_pg,
    search_memory_pg,
    search_memory_vector,
    get_recent_memories,
    run_proactive_analysis,
)

from .ai_tools import (
    get_longtracer_model,
    verify_claim,
    analyze_sentiment,
)

from .system_utils import (
    HATA_LOG,
    check_system_status,
    log_error,
    get_error_history,
    get_plan,
    remember_session,
    get_session,
    run_terminal,
    fetch_webpage,
    suggest_fix,
    get_now,
    get_weather,
    calculate_budget,
)

from .notifications import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    send_telegram_message,
    schedule_reminder,
)

from .autonomous import (
    run_autonomous,
)


__all__ = [
    # google_api
    "authenticate",
    "get_auth_url",
    "send_email",
    "read_emails",
    "add_calendar_event",
    "list_calendar_events",
    "list_drive_files",
    "upload_drive_file",
    "read_sheet",
    "write_sheet",
    "append_sheet",

    # chroma_store
    "CHROMA_HOST",
    "CHROMA_PORT",
    "search_notes",
    "add_file_to_chroma",
    "search_brain",
    "save_to_brain",

    # pg_brain
    "PG_CONFIG",
    "get_pg_connection",
    "save_memory_pg",
    "search_memory_pg",
    "search_memory_vector",
    "get_recent_memories",
    "run_proactive_analysis",

    # ai_tools
    "get_longtracer_model",
    "verify_claim",
    "analyze_sentiment",

    # system_utils
    "HATA_LOG",
    "check_system_status",
    "log_error",
    "get_error_history",
    "get_plan",
    "remember_session",
    "get_session",
    "run_terminal",
    "fetch_webpage",
    "suggest_fix",
    "get_now",
    "get_weather",
    "calculate_budget",

    # notifications
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "send_telegram_message",
    "schedule_reminder",

    # autonomous
    "run_autonomous",
]
