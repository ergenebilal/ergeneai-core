# tools.py API Referansı

**Konum:** `~/hermes_data/tools.py`
**Gereken Python:** 3.11 (`python3.11`)
**Import:** `import sys; sys.path.insert(0, '/home/hermes/hermes_data'); from tools import *`

---

## 1. `verify_claim(claim: str, source: str) -> dict`

Bir iddiayı LongTracer ile kaynağa karşı doğrular.

| Param | Tip | Açıklama |
|-------|-----|----------|
| claim | str | Doğrulanacak iddia cümlesi |
| source | str | Kaynak metin (referans veri) |

**Return:** `{"verdict": "PASS"|"FAIL", "confidence": float|None}`

**Not:** İlk çağrıda modeller yüklenir (20-25sn). Sonrakiler cache'den anında.

---

## 2. `check_system_status(service_name: str) -> dict`

Bir servisin fiziksel durumunu kontrol eder.

| Param | Tip | Açıklama |
|-------|-----|----------|
| service_name | str | "chroma" veya "docker" |

**Return:** `{"status": "running"|"not_running"|"unknown", "output": ...}`

**Desteklenen servisler:**
- `"chroma"` → `curl -sf http://localhost:8001/api/v2/heartbeat` (v2 API)
- `"docker"` → `docker ps`

---

## 3. `log_hata(hata_tipi: str, detay: str, dogru_davranis: str) -> None`

Geçmiş hata loguna kayıt ekler.

| Param | Tip | Açıklama |
|-------|-----|----------|
| hata_tipi | str | Hata kategorisi (örn: "hallüsinasyon", "soru_atlama") |
| detay | str | Ne olduğu |
| dogru_davranis | str | Doğrusu ne olmalıydı |

**Log dosyası:** `~/hermes_hata_log.txt`

---

## 4. `get_hata_gecmisi(limit: int = 5) -> list[str]`

Son N hatayı log dosyasından okur.

| Param | Tip | Açıklama |
|-------|-----|----------|
| limit | int | Kaç satır döneceği (default: 5) |

**Return:** Liste halinde log satırları. Log yoksa `[]`.

---

## 5. `bilal_notes_ara(soru: str, n_results: int = 3) -> list[str]`

ChromaDB'de `bilal_notes` koleksiyonunda semantik arama yapar.

| Param | Tip | Açıklama |
|-------|-----|----------|
| soru | str | Aranacak sorgu metni |
| n_results | int | Kaç sonuç döneceği (default: 3) |

**Return:** Doküman metinlerinin listesi. Bulunamazsa `[]`.

---

## 6. `dosya_ekle(dosya_yolu: str, koleksiyon: str = "bilal_notes") -> str`

Bir dosyayı ChromaDB koleksiyonuna ekler.

| Param | Tip | Açıklama |
|-------|-----|----------|
| dosya_yolu | str | Eklenecek dosyanın yolu |
| koleksiyon | str | Hedef koleksiyon adı (default: "bilal_notes") |

**Return:** `"{dosya_adi} eklendi."`

---

## 7. `plan_hedef(hedef: str) -> dict`

Bir hedef kelimeye göre plan döndürür (adımlar + açıklama).

| Param | Tip | Açıklama |
|-------|-----|----------|
| hedef | str | Görev tanımı (örn: "R10 kampanyasını araştır") |

**Return:** `{"adimlar": [...], "aciklama": "..."}`

**Eşleştirme:**
| hedef'te geçen | adimlar | aciklama |
|---|---|---|
| "araştır"/"arastir" | `bilal_notes_ara()`, `verify_claim()` | ChromaDB'de ara, sonra doğrula |
| "kurulum" | `check_system_status()`, `dosya_ekle()`, `log_hata()` | Sistem durumunu kontrol et, dosya ekle, hata logla |
| "rapor" | `get_hata_gecmisi()`, `bilal_notes_ara()` | Hata geçmişini al, ChromaDB'de ara |
| "kod" | `terminal_calistir()`, `verify_claim()` | Kodu çalıştır, sonucu doğrula |
| "web" | `web_cek()`, `bilal_notes_ara()`, `dosya_ekle()` | Web'den veri çek, ara, kaydet |
| (hiçbiri) | `bilal_notes_ara()`, `verify_claim()` | Genel araştırma |

---

## 8. `get_longtracer_model() -> module`

LongTracer modelini cache'leyerek döndürür (internal fonksiyon).
- İlk çağrı: `import longtracer` + model yükleme (~20sn)
- Sonraki çağrılar: cache'den anında

---

## 9. `session_hatirla(mesaj: str) -> list[str]`

Son 5 mesajı hatırlamak için oturum hafızasına ekler.

| Param | Tip | Açıklama |
|-------|-----|----------|
| mesaj | str | Kaydedilecek mesaj |

**Return:** Son 5 mesajın listesi. Internal değişken `_session_memory`.

---

## 10. `session_al() -> list[str]`

Oturum boyunca kaydedilmiş tüm mesajları döndürür.

**Return:** Tüm mesajların listesi.

---

## 11. `terminal_calistir(komut: str) -> str`

VPS'te herhangi bir komut çalıştırır (güvenlik riskine dikkat).

| Param | Tip | Açıklama |
|-------|-----|----------|
| komut | str | Çalıştırılacak komut |

**Return:** Komut çıktısı (stdout).

**Uyarı:** `komut.split()` ile parçalandığı için tırnak içi argümanlar bozulabilir.

---

## 12. `web_cek(url: str) -> str`

Bir URL'den HTTP GET ile içerik çeker.

| Param | Tip | Açıklama |
|-------|-----|----------|
| url | str | Çekilecek URL |

**Return:** İlk 1000 karakter.

---

## 13. `self_repair(hata_mesaji: str, deneme: int = 1) -> str`

Hata mesajına göre alternatif aksiyon önerir.

| Param | Tip | Açıklama |
|-------|-----|----------|
| hata_mesaji | str | Hata metni |
| deneme | int | Kaçıncı deneme (default: 1) |

**Return:** Önerilen aksiyon metni.

**Davranış:**
- 3+ deneme (>=3) → "Maksimum deneme aşıldı, manuel müdahale gerekli"
- "chromadb"/"chroma" içeren hata → restart önerisi (`chroma run --host 0.0.0.0 --port 8001 &`)
- "dosya" + "yok" → dosya oluşturma önerisi
- "bağlantı"/"connection" → bağlantı kontrolü (`curl -I https://httpbin.org`)
- Diğer → alternatif deneme mesajı + deneme sayısı

---

## Örnek Kullanım

```python
# Konuşma başında
from tools import get_hata_gecmisi, bilal_notes_ara, verify_claim, plan_hedef, session_hatirla, self_repair

# 1. Geçmiş hataları kontrol et
hatalar = get_hata_gecmisi(5)
if hatalar:
    print("Önceki hatalar:", hatalar)

# 2. Hedefe göre adımları planla
adimlar = plan_hedef("R10 kampanyasını araştır")
print("Plan:", adimlar)

# 3. ChromaDB'de ara
bulgular = bilal_notes_ara("R10 kampanya kuralları", n_results=3)

# 4. Cevabı doğrula
for bulgu in bulgular:
    sonuc = verify_claim("R10'da link yasak", kaynak=bulgu)
    if sonuc.get("verdict") == "FAIL":
        print("Uyarı: Bu iddia doğrulanamadı, cevaba ekleme")
```
