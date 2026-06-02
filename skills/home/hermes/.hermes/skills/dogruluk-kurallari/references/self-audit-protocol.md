# Self-Audit Protocol (agent-architecture-audit entegrasyonu)

## Ne Zaman?
- Her konuşma SONUNDA — 4 sözü kontrol et
- Haftada 1 — tam 12 katman denetimi
- Kullanıcı "tutarsız" veya "çelişkili" dediğinde
- Aynı hata türü 2. kez tekrarladığında

## Konuşma Sonu Kontrolü (4 Söz)

4 sözü tek tek kontrol et:
1. tools.py import edildi mi? → hata_gecmisi alındı mı? ChromaDB sorgusu var mı?
2. Fiziksel kontrol yapıldı mı? → terminal çıktısı var mı? (curl/ps aux/docker ps)
3. Hata varsa log_hata() kaydedildi mi?
4. Çelişkili cevap verildi mi? → Aynı konuda önce X, sonra not X?

Sonuçları ChromaDB'ye kaydet: log_hata('oz-degerlendirme', 'Sözler: 3/4 tutuldu', 'hepsini tuttur')

## Haftalık Tam Denetim (agent-architecture-audit)
1. System prompt — tools.py import otomatik mi? 4 söz okunuyor mu?
2. Session history — önceki turda aynı konuda farklı cevap var mı?
3. Long-term memory — memory'deki eski not yeni kararla çelişiyor mu?
6. Tool selection — skill_view atlandı mı? check_system_status çağrıldı mı?
7. Tool execution — verify_claim çağrıldı mı? FAIL sonucuna uyuldu mu?
11. Hidden repair — "yaptım" deyip yapmadığın söz var mı?

## Denetim Geçmişi
Her denetim log_hata('oz-degerlendirme', ...) ile ChromaDB'ye kaydedilir.
