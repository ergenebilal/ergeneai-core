---
name: proactive-intelligence
version: 1.0.0
description: Scheduled intelligence briefing systems — cron-triggered data collection, local LLM analysis, and formatted report delivery via Hermes cron jobs
---

# Proactive Intelligence System

Pattern for building automated intelligence briefing systems: collect data from memory/storage on a schedule, analyze with a local LLM, and deliver a structured report to the user.

## Architecture

```
Cron Trigger (e.g. 08:30 TR daily)
  → Agent loads tools.py
  → pg_proaktif_analiz() or custom collector
  → Collects recent records from PostgreSQL
  → Sends to local LLM (Ollama) for analysis
  → Returns structured 3-part briefing
  → Cron job auto-delivers via Telegram
```

## Core Pattern: Database → LLM → Report

### 1. Data Collection Function (in tools.py)

```python
def pg_proaktif_analiz() -> dict:
    \"\"\"Son 48 saatteki kayitlari analiz edip 3 maddelik ozet cikarir.\"\"\"
    # Query PostgreSQL for recent strategic records
    records = query_pg(
        "SELECT content, category, created_at FROM hermes_memory "
        "WHERE category IN ('tech_note', 'business_strategy') "
        "AND created_at > NOW() - INTERVAL '48 hours'"
    )
    if not records:
        return {"ozet": "Yeni kayit yok.", "kayit_sayisi": 0}

    # Format for LLM
    kayit_metni = "\n".join([
        f"[{r[1]}] {str(r[2])[:10]}: {r[0][:300]}" for r in records
    ])

    # Analyze with local LLM
    response = ollama.chat(
        model='qwen2.5:3b',  # 3.1B, Q4_K_M, local, free
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0.3, 'num_predict': 500}
    )

    return {"ozet": response['message']['content'], "kayit_sayisi": len(records)}
```

### 2. Cron Job Creation

```bash
# Schedule: use UTC in cron expression (TR = UTC+3)
# Example: 08:30 TR = "30 5 * * *"
hermes cron create \
  --name "Gunluk Brifing" \
  --schedule "30 5 * * *" \
  --deliver origin \
  --workdir /home/hermes/hermes_data \
  --prompt "tools.py'nin pg_proaktif_analiz() fonksiyonunu cagir..."
```

## Prompt Template for Analysis LLM

```
Sen [sistem adi] proaktif analiz motorusun. Asagidaki son 48 saatte kaydedilmis notlari analiz et ve [kullanici] icin TURKCE olarak 3 bolumlu bir ozet cikar:

1. BU GUNUN ODAK NOKTASI (En kritik 1-2 madde)
2. FIRSATLAR (Kaldiraca donusturulebilecek girdiler)
3. OPERASYONEL RISKLER (Aksiyon gerektiren tehditler)

NOTLAR:
{kayit_metni}

CEVAP FORMATI (TURKCE):
**Gunun Odak Noktasi**
- ...

**Firsatlar**
- ...

**Operasyonel Riskler**
- ...
```

## Pitfalls

- **Local LLM quality**: Qwen2.5 3B produces functional but occasionally repetitive analysis. For higher quality, use a larger model (7B+) or an API model. Temperature 0.3 balances creativity vs. precision.
- **Database category coverage**: Only records with matching categories (`tech_note`, `business_strategy`) are included. If the user saves notes under different categories, update the SQL query.
- **No records on first run**: The function handles empty results gracefully but the user should have saved at least one note before the cron fires.
- **Cron timezone**: Hermes cron uses UTC. TR (UTC+3) means 08:30 TR → `30 5 * * *`. Always verify with `date -u` on the server.
- **Workdir**: Always set `workdir=/home/hermes/hermes_data` so the cron can import tools.py without path issues.
- **Flush stdout**: When testing locally, use `print(..., flush=True)` — buffered stdout can appear as a hang in terminal output.
- **import tools.py**: The `tools.py` startup print ("✅ tools.py yuklendi...") is harmless but consumes context. Suppress with `contextlib.redirect_stdout` only if it causes issues — normal import works fine.
- **Ollama resource usage**: 3B model uses ~2GB RAM, ~2s per analysis. On a server with limited RAM, monitor with `htop`. Consider scheduling briefing at low-traffic times.

## Reference Files

- `references/ergeneai-proactive-briefing.md` — Real-world implementation: Ollama-based daily briefing for ErgeneAI with 48-hour PG memory analysis, 3-part Turkish output. Includes test output and cron configuration.
