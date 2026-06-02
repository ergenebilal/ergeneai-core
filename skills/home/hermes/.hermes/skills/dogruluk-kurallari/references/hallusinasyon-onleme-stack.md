# Hallüsinasyon Önleme Stack (1 Haziran 2026)

## 3 Katmanlı Doğrulama Sistemi

### Katman 1 — ChromaDB + tools.py (HER KONUŞMADA AKTİF)
- `bilal_notes_ara(sorgu)` — iddia etmeden önce kaynak dokümanlarda ara
- `get_hata_gecmisi(5)` — geçmiş hataları hatırla, tekrarlama
- `check_system_status('chroma')` — sistem çalışıyor mu doğrula
- Her konuşma başında `dogruluk-kurallari` skill'i ile otomatik yüklenir
- 4 söz: `hermes_gelisim` koleksiyonundan okunur

### Katman 2 — LongTracer (ANLIK DOĞRULAMA)
```python
from tools import verify_claim

r = verify_claim('iddia', kaynak='kaynak metin')
if r['verdict'] == 'FAIL':
    # Bu iddiayı cevaba EKLEME
    # Veya: "Kesin değilim, kaynakla çelişiyor" de
```
- STS + NLI hibrit, LLM çağırmaz
- Model cache'li (ilk çağrı ~15sn, sonraki ~0sn)
- verdict=PASS/FAIL/UNKNOWN döndürür
- FAIL: iddia kaynak dokümanla uyuşmuyor

### Katman 3 — agent-architecture-audit (PERİYODİK DENETİM)
ECC skill: `skill_view(name='agent-architecture-audit')`
12 katmanlı ajan denetimi:
1. System prompt — 4 söz okundu mu?
2. Session history — çelişkili cevap var mı?
6. Tool selection — skill_view atlandı mı?
7. Tool execution — verify_claim çağrıldı mı?
11. Hidden repair — "yaptım" deyip yapmadığın söz var mı?

## Hızlı Başvuru
| Durum | Ne yap | Katman |
|-------|--------|--------|
| "X çalışıyor" diyeceksin | `check_system_status('x')` | 1 |
| "X'te fırsat var" diyeceksin | `bilal_notes_ara('x')` | 1 |
| Cevabın doğruluğundan emin değilsin | `verify_claim()` | 2 |
| Haftalık kendini denetle | `agent-architecture-audit` | 3 |
| Aynı hata tekrarlıyor | `get_hata_gecmisi()` | 1 |

## Önemli
- FAIL = iddia kaynakla uyuşmuyor. Düzelt veya çıkar.
- UNKNOWN = kaynak yok. Tahmin etme, "bilmiyorum" de.
- PASS = kaynakla uyumlu. Ama kaynağın kendisi yanlış olabilir.
