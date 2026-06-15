"""
Notifications module.
Handles Telegram messaging and scheduled reminders (threading.Timer based).
"""

import threading
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# === CONFIGURATION ===
TELEGRAM_BOT_TOKEN = "8654902345:***"
TELEGRAM_CHAT_ID = "5506784207"

# === Active reminders tracker ===
_active_reminders: dict = {}
_active_reminders_lock = threading.Lock()
_MAX_CONCURRENT = 10


def send_telegram_message(message: str) -> bool:
    """Sends a message to Telegram.

    Args:
        message: Message text to send

    Returns:
        bool: True if successful
    """
    try:
        import requests

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        r = requests.post(url, json=data, timeout=10)
        return r.json().get("ok", False)
    except requests.RequestException as e:
        logger.warning("Telegram send failed: %s", e)
        return False
    except Exception as e:
        logger.error("Telegram send unexpected error: %s", e)
        return False


def schedule_reminder(
    message: str,
    minutes_later: int,
    reminder_id: Optional[str] = None,
) -> str:
    """Sets a reminder using threading.Timer (no busy-wait sleep).

    Args:
        message: Reminder message text
        minutes_later: How many minutes later to fire
        reminder_id: Optional unique ID for cancellation (default: auto-generated)

    Returns:
        str: Success or error message
    """
    if minutes_later < 0:
        return "❌ Reminder error: minutes_later cannot be negative"

    if reminder_id is None:
        reminder_id = f"reminder_{id(message)}_{minutes_later}"

    if not message.strip():
        return "❌ Reminder error: empty message"

    with _active_reminders_lock:
        if reminder_id in _active_reminders:
            return f"❌ Reminder '{reminder_id}' already active"

        if len(_active_reminders) >= _MAX_CONCURRENT:
            return (
                f"❌ Maximum {_MAX_CONCURRENT} concurrent reminders reached, "
                f"'{reminder_id}' rejected"
            )

        def _fire(tid: str, msg: str):
            """Timer callback — sends message then cleans up."""
            try:
                send_telegram_message(f"⏰ REMINDER: {msg}")
            except Exception as exc:
                logger.error("Reminder[%s] fire error: %s", tid, exc)
            finally:
                with _active_reminders_lock:
                    _active_reminders.pop(tid, None)

        timer = threading.Timer(
            interval=minutes_later * 60.0,
            function=_fire,
            args=(reminder_id, message),
        )
        timer.daemon = True
        _active_reminders[reminder_id] = {
            "timer": timer,
            "message": message,
            "minutes": minutes_later,
        }

    timer.start()
    logger.info(
        "Reminder '%s' set: %d min later \"%s\"", reminder_id, minutes_later, message
    )
    return f"⏰ Reminder set ({reminder_id}): {minutes_later} min later \"{message}\""


def cancel_reminder(reminder_id: str) -> bool:
    """Cancels an active reminder by ID.

    Args:
        reminder_id: The reminder ID to cancel

    Returns:
        bool: True if successfully cancelled, False if not found
    """
    with _active_reminders_lock:
        entry = _active_reminders.pop(reminder_id, None)
        if entry is None:
            logger.warning("cancel_reminder: '%s' not found", reminder_id)
            return False
        entry["timer"].cancel()

    logger.info("cancel_reminder: '%s' cancelled", reminder_id)
    return True


def get_active_reminder_ids() -> list:
    """Returns list of active reminder IDs."""
    with _active_reminders_lock:
        return list(_active_reminders.keys())


def get_active_reminder_count() -> int:
    """Returns count of active reminders."""
    with _active_reminders_lock:
        return len(_active_reminders)


def clear_all_reminders():
    """Cancels all active reminders."""
    with _active_reminders_lock:
        ids = list(_active_reminders.keys())
        for rid in ids:
            entry = _active_reminders.pop(rid, None)
            if entry:
                entry["timer"].cancel()
    logger.info("clear_all_reminders: %d reminder(s) cancelled", len(ids))
