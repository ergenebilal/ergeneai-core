# Hermes Öz Değerlendirme ve Skor Kartı Sistemi

## Ne Zaman Yapılır?
- Bilal "kendini değerlendir" dediğinde
- Bilal "durum" dediğinde
- `hermes_skor_karti` alias'ı çağrıldığında
- Haftada bir otomatik (planlanmış)

## Skor Kartı JSON Formatı

Dosya: `/home/hermes/hermes_data/hermes_skor_karti.json`

```json
{
  "tarih": "2026-06-02",
  "genel_skor": 57,
  "onceki_skor": null,
  "degisim": null,
  "hedef_skor": 85,
  "kategoriler": {
    "altyapi": {"puan": 100, "detay": "port acik", "aciklama": "..."},
    "hafiza": {"puan": 36, "detay": "9 kayit", "aciklama": "..."},
    "embedding_daemon": {"puan": 100, "detay": "uptime", "aciklama": "..."},
    "proaktif": {"puan": 50, "detay": "brifing cron'u", "aciklama": "..."},
    "test_kalitesi": {"puan": 0, "detay": "57 fonk, 0 test", "aciklama": "..."},
    "karar_motoru": {"puan": 5, "detay": "analiz var kullanilmiyor", "aciklama": "..."}
  }
}
```

## Puan Hesaplama

| Kategori | Formül |
|---|---|
| Altyapı | (açık port / 5) * 100 |
| Hafıza | min(100, kayit_sayisi / 100 * 100) ama <10→40, 10-30→60, 30+→80 |
| Embedding Daemon | 100 (çalışıyorsa), 0 (kapalıysa) |
| Proaktif | min(100, son24h_kayit * 11) |
| Test | min(100, test_sayisi * 10) |
| Karar Motoru | 0-100 (var olması 20, kullanılıyor olması 40) |

## 10 Soruluk Değerlendirme Protokolü

Yanıt kuralları:
- İltifat etme. Motivasyon konuşması yapma.
- Ölçülebilir ve eleştirel cevap ver.
- Canlı veri topla (terminal + curl + python ile).
- Her iddiayı kanıtla.

Sorular (sırasıyla cevapla):
1. Dün nasıldın, bugün nasılsın? — operasyonel değişim
2. En büyük gelişimin ne oldu? — tek cümle
3. Hâlâ hangi konularda zayıfsın? — tablo: zayıflık + kanıt
4. Bilal "durum" dese kaç/10 faydalı olursun? — ne verebilirim / ne veremem
5. Kendini % kaç olgun görüyorsun? — kategori bazlı tablo
6. Seni %100'e yaklaştıracak 5 şey? — sıralı, gerekçeli
7. Kendini ne olarak görüyorsun? — chatbot/asistan/analist/COO
8. Bilal'in fark etmediği en önemli risk? — finansal risk varsa belirt
9. Bilal'in fark etmediği en önemli fırsat? — ürünleştirme varsa belirt
10. Tek geliştirme hakkı? — gerekçesiyle
