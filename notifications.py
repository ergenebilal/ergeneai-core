#!/usr/bin/env python3.11
"""
NOTIFICATIONS — Thread hatirlatici modulu (SORUN 6)
===================================================
schedule_reminder() fonksiyonu threading.Timer kullanarak
zamanlanmis hatirlatici calistirir. Iptal edilebilir,
maksimum 10 eszamanli hatirlatici ile sinirlidir.
"""

import threading
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# === Global hatirlatici takibi ===
# _active_reminders[reminder_id] = {"timer": threading.Timer, "target": callable, "args": tuple, "kwargs": dict}
_active_reminders: dict = {}
_active_reminders_lock = threading.Lock()
_MAX_CONCURRENT = 10


def schedule_reminder(
    reminder_id: str,
    delay: float,
    target: Callable,
    args: Optional[tuple] = None,
    kwargs: Optional[dict] = None,
) -> bool:
    """
    threading.Timer ile zamanlanmis hatirlatici baslatir.
    
    Args:
        reminder_id: Hatirlatici kimligi (iptal icin kullanilir)
        delay: Bekleme suresi (saniye)
        target: Calistirilacak fonksiyon
        args: Fonksiyona gonderilecek pozisyonel argumanlar (default: ())
        kwargs: Fonksiyona gonderilecek keyword argumanlar (default: {})
    
    Returns:
        bool: Basarili mi (False = limit asimi veya ayni ID zaten var)
    
    Ornek:
        schedule_reminder("demo", 10, print, args=("10 sn gecti!",))
    """
    global _active_reminders

    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}

    if delay < 0:
        logger.warning("schedule_reminder: negatif delay (%s), 0 olarak ayarlandi", delay)
        delay = 0.0

    with _active_reminders_lock:
        # Ayni ID'den varsa yenisini ekleme
        if reminder_id in _active_reminders:
            logger.warning("schedule_reminder: '%s' zaten aktif, atlaniyor", reminder_id)
            return False

        # Maksimum limit kontrolu
        if len(_active_reminders) >= _MAX_CONCURRENT:
            logger.warning(
                "schedule_reminder: maksimum %d hatirlatici limitine ulasildi, '%s' atlaniyor",
                _MAX_CONCURRENT,
                reminder_id,
            )
            return False

        def _wrapper(tid: str, fn: Callable, fn_args: tuple, fn_kwargs: dict):
            """Hatirlatici calistiktan sonra _active_reminders'tan temizler."""
            try:
                fn(*fn_args, **fn_kwargs)
            except Exception as exc:
                logger.error("schedule_reminder[%s] hatasi: %s", tid, exc, exc_info=True)
            finally:
                with _active_reminders_lock:
                    _active_reminders.pop(tid, None)

        timer = threading.Timer(
            interval=delay,
            function=_wrapper,
            args=(reminder_id, target, args, kwargs),
        )
        timer.daemon = True

        _active_reminders[reminder_id] = {
            "timer": timer,
            "target": target,
            "args": args,
            "kwargs": kwargs,
        }

    timer.start()
    logger.info("schedule_reminder: '%s' baslatildi (%s sn)", reminder_id, delay)
    return True


def cancel_reminder(reminder_id: str) -> bool:
    """
    Zamanlanmis bir hatirlaticiyi iptal eder.
    
    Args:
        reminder_id: Iptal edilecek hatirlatici kimligi
    
    Returns:
        bool: Basarili mi (False = boyle bir hatirlatici yok)
    """
    with _active_reminders_lock:
        entry = _active_reminders.pop(reminder_id, None)
        if entry is None:
            logger.warning("cancel_reminder: '%s' bulunamadi", reminder_id)
            return False
        timer = entry["timer"]
        timer.cancel()

    logger.info("cancel_reminder: '%s' iptal edildi", reminder_id)
    return True


def get_active_reminder_ids() -> list:
    """Aktif hatirlatici ID'lerini dondurur."""
    with _active_reminders_lock:
        return list(_active_reminders.keys())


def get_active_reminder_count() -> int:
    """Aktif hatirlatici sayisini dondurur."""
    with _active_reminders_lock:
        return len(_active_reminders)


def clear_all_reminders():
    """Tum hatirlaticilari iptal eder ve temizler."""
    with _active_reminders_lock:
        ids = list(_active_reminders.keys())
        for rid in ids:
            entry = _active_reminders.pop(rid, None)
            if entry:
                entry["timer"].cancel()
    logger.info("clear_all_reminders: %d hatirlatici iptal edildi", len(ids))
