#!/usr/bin/env python3
"""
ergeneai_tools.py — ErgeneAI Tools Facade

Backward-compatible facade that re-exports all functions from the core/ package.
The old tools.py has been refactored into modular core/ structure.

Usage:
    from ergeneai_tools import search_notes, run_terminal, send_email
    # or import the old way: from ergeneai_tools import bilal_notes_ara  (deprecated)

Migration guide:
    Old (deprecated)           → New (recommended)
    ----------------------------→-------------------------------
    bilal_notes_ara()          → search_notes()
    dosya_ekle()               → add_file_to_chroma()
    beyin_ara()                → search_brain()
    beyin_kaydet()             → save_to_brain()
    pg_baglan()                → get_pg_connection()
    pg_kaydet()                → save_memory_pg()
    pg_ara()                   → search_memory_pg()
    pg_ara_vector()            → search_memory_vector()
    pg_son()                   → get_recent_memories()
    pg_proaktif_analiz()       → run_proactive_analysis()
    google_auth()              → authenticate()
    google_auth_link()         → get_auth_url()
    gmail_gonder()             → send_email()
    gmail_oku()                → read_emails()
    takvim_etkinlik_ekle()     → add_calendar_event()
    takvim_etkinlik_listele()  → list_calendar_events()
    drive_dosya_listele()      → list_drive_files()
    drive_dosya_yukle()        → upload_drive_file()
    sheets_oku()               → read_sheet()
    sheets_yaz()               → write_sheet()
    sheets_ekle()              → append_sheet()
    log_hata()                 → log_error()
    get_hata_gecmisi()         → get_error_history()
    plan_hedef()               → get_plan()
    session_hatirla()          → remember_session()
    session_al()               → get_session()
    terminal_calistir()        → run_terminal()
    web_cek()                  → fetch_webpage()
    self_repair()              → suggest_fix()
    suan()                     → get_now()
    hava_durumu()              → get_weather()
    hesap_hesapla()            → calculate_budget()
    telegram_mesaj_gonder()    → send_telegram_message()
    hatirlatici_kur()          → schedule_reminder()
    otonom_calistir()          → run_autonomous()
    analiz_et()                → analyze_sentiment()
"""

import sys
import os

# Add parent dir to path so core/ package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import *

# ── Built-in test on import ──
if __name__ == "__main__":
    print("✅ ergeneai_tools.py yuklendi. Mevcut fonksiyonlar (Ingilizce):")
    funcs = [name for name in dir() if not name.startswith("_")]
    for f in sorted(funcs):
        print(f"   - {f}")
    print(f"\nToplam: {len(funcs)} fonksiyon")
