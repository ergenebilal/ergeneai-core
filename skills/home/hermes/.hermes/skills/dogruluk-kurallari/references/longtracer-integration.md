# LongTracer Entegrasyonu

## Kurulum
```bash
pip install longtracer
```
tools.py'de import edildi, `verify_claim()` wrapper'ı hazır.

## API
```python
from longtracer import CitationVerifier

verifier = CitationVerifier()
result = verifier.verify(
    response='Gumroad API anahtari rK_xxxx ile baslar.',
    sources=['Gumroad API anahtari ornek: rK_xxxx...']
)
# result.verdict = 'PASS' veya 'FAIL'
# result.trust_score = 0.0 - 1.0
# result.hallucination_count = 0 veya 1+
# result.all_supported = True/False
# result.flagged_claims = [] — flag'lenen iddialar
```

## Cache Mekanizmasi (KRITIK)
Modeller her `CitationVerifier()` cagrisinda yuklenir (~7sn).
tools.py'de `get_verifier()` ile cache'lenmistir:

```python
_longtracer_verifier = None

def get_verifier():
    global _longtracer_verifier
    if _longtracer_verifier is None:
        from longtracer import CitationVerifier
        _longtracer_verifier = CitationVerifier()
    return _longtracer_verifier
```

## tools.py'deki wrapper
```python
from tools import verify_claim

# Direkt kaynak ile
r = verify_claim('PilotDeck calisiyor', kaynak='PilotDeck 1 Haziranda kapaliydi')
# → verdict=FAIL trust=0.68

# ChromaDB'den otomatik bul
r = verify_claim('Gumroad API rK_xxxx', chromadb_sorgu='Gumroad')
# → verdict=PASS trust=0.99

# Kaynak yoksa UNKNOWN doner
r = verify_claim('X calisiyor')
# → verdict=UNKNOWN message=Karsilastirma kaynagi yok
```

## Model Detaylari
- STS modeli: all-MiniLM-L6-v2 (80MB)
- NLI modeli: deberta-v3-xsmall (250MB)
- Model cache omru: session boyunca (tools.py import edildigi surece)
- Sadece LOCAL calisir, API gerektirmez
- LLM cagirmaz, STS+NLI ile semantik karsilastirma yapar

## Cikti Ornekleri
```
verdict=PASS trust=0.88 hallucination_count=0 all_supported=True
verdict=FAIL trust=0.48 hallucination_count=1 all_supported=False
```

## Uyari
FAIL sonucu = iddia KESIN yanlis degil, kaynakla uyusmuyor.
Eminsen alternatif kaynak bul, yoksa "Kesin degilim" de.
