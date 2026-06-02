---
name: personal-finance
description: Structured personal finance planning — debt triage, income projection, payment calendar, and scenario planning for irregular-income workers (couriers, freelancers, gig economy).
version: 1.0.0
author: Hermes Agent
tags: [finance, planning, debt, income, budgeting]
---

# Personal Finance Planning

## Overview

Structured financial planning for users with **irregular daily income** (couriers, freelancers, gig workers). Focuses on short-term cash-flow management, debt repayment scheduling, and income targeting rather than long-term investment.

**Core principle:** For irregular-income workers, the unit of planning is the DAY (how much to earn today), not the MONTH. Plans must account for daily minimums, weekly fatura cycles, and lump-sum payment dates.

## When to Use

- User shares debt/income numbers and asks for a plan
- User sets a weekly or monthly income target
- User mentions multiple payment obligations with different due dates
- User is in a cash crunch and needs triage

## Trigger Phrases

- "hesap kitap yapalım"
- "borç durumu şöyle"
- "bu ay sıkışığım"
- "şu kadar kazanmam lazım"
- "para lazım"

## Procedure

### Phase 1: Data Collection

Gather ALL of the following before making any calculations:

1. **Income pattern:**
   - Daily earnings (today's actual)
   - Packages/deliveries per day
   - Pay cycle (weekly fatura? bi-weekly? daily?)
   - Payment delay (when does money hit the account?)
   - Maximum realistic daily capacity

2. **Debt inventory:**
   - Credit cards (balance + due date + minimum payment %)
   - KMH/overdraft (balance + due date)
   - Loans (installment + due date)
   - Insurance payments (amount + expiry date)
   - Other (KDV, invoices, informal debts)

3. **Fixed costs:**
   - Fuel/gas (daily or weekly)
   - Food
   - Rent if applicable
   - Phone/data

4. **Timeline:**
   - "By when do you need to be clean?" (debt-free date)
   - Critical dates (insurance expiry, credit card last payment day)

### Phase 2: Triage

Rank obligations by **consequence of missing**:

| Priority | Type | Consequence |
|----------|------|-------------|
| 🔴 Critical | Motorcycle insurance expiry | Cannot work → zero income |
| 🔴 Critical | Credit card minimum payment | Late fees, credit score hit, legal action |
| 🟡 High | KMH/overdraft | Daily interest accrual |
| 🟢 Normal | Non-urgent invoices | Can defer |

**HARD RULE:** Insurance > Minimum payments > KMH > Everything else. A bike that can't ride produces zero income.

### Phase 3: Cash Flow Calendar

Build a day-by-day timeline:

```
Day X:     Income Y TL
Day X+2:   Payment Z due (card minimum)
Day X+5:   Income Y TL (next batch)
Day X+7:   Payment W due (KMH)
```

**Key insight:** For fatura-based workers (pay on Wednesday for previous week's work), the first week of a month is the tightest because you're waiting for the first payment to hit.

### Phase 4: Scenario Planning

Always present 2-3 scenarios:

- **Plan A (Conservative):** Minimum realistic daily income × days available.
- **Plan B (Target):** Stretch daily target × days.
- **Plan C (Hybrid):** Combine primary income + one-off sales (AI services, freelance). "If you sell one X package for Y TL, your daily target drops to Z."

### Phase 5: Daily Checkpoint Formula

Give the user a **daily formula** they can mentally calculate while working:

```
Daily need = (Obligations this week ÷ Days remaining this week)
```

## Communication Style

- **Lead with numbers** — front-load the math, not explanation
- **Bullet points, not paragraphs** — user reads fast between deliveries
- **Always show both optimistic and pessimistic** — gig income is volatile
- **Never say "don't worry"** — the user is worried, validate that
- **Time-aware** — check current time before greetings/signoffs.

## Common Pitfalls

### Ignoring payment delay
A fatura cut Monday pays Wednesday. The user might have earned money but cannot access it. Plan for settlement lag.

### Assuming 7-day weeks
Gig workers may have mandatory rest days, sıralama system limits, or weather downtime. Always ask: "How many days this week can you actually work?"

### Forgetting variable costs
- Fuel cost scales with deliveries
- Food is more expensive when working (no time to cook)
- Phone data for navigation

### Insurance expiry is an emergency
When motorcycle insurance expires, the bike cannot legally operate. Flag it even if the user doesn't mention it.

## Reference Files

- `references/bilal-finans-haziran-2026.md` — session-specific debt/income data for the ErgeneAI/Bilal user. Load before any financial planning session to skip the data collection phase.

### Related Scripts (hermes_data/)

Built during session for automated financial tracking:

| Script | Purpose | Cron (TR) |
|--------|---------|-----------|
| `predict.py` | Early warning — checks if ChromaDB has enough data about upcoming critical dates | 11:20 TR |
| `haziran_plani.py` | Daily financial plan — counts days to each payment, calculates daily savings needed | 10:30 TR |
| `kritik_uyari.py` | Date-based alerts (3 days before, last day, overdue) | 14:15 TR |
| `hermes_calendar.py` | Event calendar (add, list today, list upcoming, mark done) | On demand |
| `tools.py` | 19 functions including `hesap_hesapla()`, `suan()`, `analiz_et()` | Import |

**Quick test:**
```bash
python3.11 -c "
import sys; sys.path.append('/home/hermes/hermes_data')
from tools import hesap_hesapla, suan
print(suan())
print(hesap_hesapla('gider', 9000, 11))"

## Calendar Integration

Use `hermes_calendar.py` (improved version, renamed from `calendar.py` to avoid stdlib collision) or `takvim.py` (original, still works). Both share the same JSON file `~/hermes_calendar.json`:

```python
# ONCE stdlib calendar'i yukle (cache'e al)
import calendar
# SONRA path ekle ve user'in takvimini yukle
import sys; sys.path.insert(0, '/home/hermes/hermes_data')
from hermes_calendar import takvim_ekle, takvim_bugun, takvim_sonraki, takvim_tamamla

# Borc/odeme gunlerini takvime ekle
takvim_ekle("Denizbank asgari odeme", "2026-06-11", "09:00", "odeme")
takvim_ekle("YK KMH odeme", "2026-06-15", "09:00", "odeme")

# Her sabah: bugunun yapilacaklarini kontrol et
takvim_bugun()

# Onumuzdeki 7 gun
takvim_sonraki(7)

# Tamamla
takvim_tamamla("Denizbank asgari odeme")
```

Takvim verisi `~/hermes_calendar.json`'da saklanir.

## Critical Date Auto-Warning System

Don't rely on manual date tracking. The system has a dedicated auto-warning pipeline:

1. **Predict system** (`predict.py`): Checks if ChromaDB has enough data about upcoming obligations. If not, warns: "Bu konuda hiç belgen yok, acil bilgi topla!"
2. **Cron crontab** (`crontab -l`'de kayıtlı): 
   - 10:30 TR → `haziran_plani.py` (günlük plan bildirimi)
   - 11:20 TR → `predict.py` (tahmin + erken uyarı)
   - 14:15 TR → `kritik_uyari.py` (3 gün kala ⚠️)
3. **Script logic:** 3 gün kala ⚠️, son gün 🔴, geçtiyse ❌ uyarısı verir
4. **Delivery:** Telegram (Nexus bot) üzerinden direkt Bilal'e gider

**Time zone:** All cron jobs are in **Europe/Istanbul** (TR time). The system was originally UTC and had to be migrated:
```bash
sudo timedatectl set-timezone Europe/Istanbul
```

**Data:** `kritik_uyari.py` ve `haziran_plani.py` içindeki dictionary'ler manuel güncellenir:

```python
# haziran_plani.py icindeki yapi:
PLAN = {
    "Denizbank": {"tarih": "2026-06-11", "tur": "gider", "miktar": 5000},
    "Sigorta": {"tarih": "2026-06-14", "tur": "gider", "miktar": 3500},
    "KMH": {"tarih": "2026-06-15", "tur": "gider", "miktar": 2000},
}
```

## Python Version Note

All tools.py functions (ChromaDB, LongTracer, sentence-transformers) require **Python 3.11**. The system's default `python3` is 3.10. Always use `python3.11` explicitly:

```bash
# DOĞRU:
python3.11 /home/hermes/hermes_data/kritik_uyari.py

# YANLIŞ (patal, ModuleNotFoundError):
python3 /home/hermes/hermes_data/kritik_uyari.py
```

## Verification

Before presenting a plan, check:
- [ ] All debts collected (cards, KMH, insurance, informal)
- [ ] Payment due dates confirmed
- [ ] Income timing (when does money actually arrive?)
- [ ] Daily realistic max (capacity limit)
- [ ] 2-3 scenarios offered
- [ ] User's preferred language (Turkish → respond in Turkish naturally)
