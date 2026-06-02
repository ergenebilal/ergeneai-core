# ErgeneAI Proactive Briefing — Implementation Reference

## System Components

| Component | Technology | Purpose |
|---|---|---|
| Memory Store | PostgreSQL + pgvector | Stores notes with 384d embeddings |
| Local LLM | Ollama + qwen2.5:3b (3.1B, Q4_K_M) | Analyzes notes, generates Turkish briefing |
| Cron Engine | Hermes cron (UTC-based scheduling) | Triggers daily at 08:30 TR |
| Delivery | Telegram (via cron `deliver: origin`) | Auto-sends formatted report |

## Database Query

```python
# Son 48 saat, sadece stratejik kategoriler
cur.execute(
    "SELECT content, category, created_at FROM hermes_memory "
    "WHERE category IN ('tech_note', 'business_strategy') "
    "AND created_at > NOW() - INTERVAL '48 hours' "
    "ORDER BY created_at DESC"
)
```

## LLM Prompt (Turkish, structured 3-part output)

The prompt instructs the LLM to produce exactly 3 sections with markdown bold headers:

```
**Gunun Odak Noktasi**
- ...

**Firsatlar**
- ...

**Operasyonel Riskler**
- ...
```

Temperature: 0.3 (balances consistency with minimal creativity)
Max tokens: 500 (enough for 3 sections with bullet points)

## Test Output (2 June 2026)

6 kayıt analiz edildi. LLM çıktısı:

```
**Gunun Odak Noktasi**
Bu günün odak noktası, Bilal kuryelikten kurtulmak isteyen hedefini ve n8n Bridge testiyle ilgili bilgiye odaklanmaktadır.

**Firsatlar**
Hermes ikinci beyin PostgreSQL tabanlı olup 2 Haziran 2026 tarihinde kurulmuş. n8n Hermes Output Parser & Router sistemi de oluşturulmuştur.

**Operasyonel Riskler**
1. Teknoloji kullanımının doğru şekilde gerçekleştirilip gerçekleştirilmediği
2. PostgreSQL ile semantik aramanın işlevselliği
3. Sistem stabilitesi
```

## Cron Configuration (Created 2 June 2026)

```yaml
name: Proaktif Sabah Brifingi
schedule: "30 5 * * *"    # 08:30 TR (UTC+3)
deliver: origin           # Auto-deliver to Telegram
workdir: /home/hermes/hermes_data
job_id: 6112b06ca321
```

The cron prompt instructs the agent to:
1. Import tools.py
2. Call `tools.pg_proaktif_analiz()`
3. Format the output with **📊 Günaydın Bilal! Bugünün Stratejik Raporu** header
4. Deliver the briefing

## Adding New Categories

To include additional note categories in the briefing, update the SQL IN clause:

```python
"WHERE category IN ('tech_note', 'business_strategy', 'user_preference')"
```
