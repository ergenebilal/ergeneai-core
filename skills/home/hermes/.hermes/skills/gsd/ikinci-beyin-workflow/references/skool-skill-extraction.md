# Skool'dan Skill Çıkarma Workflow'u

Skool'daki ücretli eğitimlerden (özellikle Digital Academy / Mert Durmazer) değerli bilgileri çekip Hermes skill'ine dönüştürme prosedürü.

## Kaynak

- **Digital Academy** (skool.com/otomasyon) — $39/ay, Mert Durmazer
- **Youtubersin** (skool.com/youtubersin-5566) — Ersin Seven (daha az değerli)

## Adımlar

### 1. Giriş
- Bilal'den Skool email + şifre al (konuşmada kalır, memory'e kaydedilmez)
- Browser ile skool.com/login → credentials gir → oturum aç

### 2. Topluluk Keşfi
- Sol menüdeki toplulukları kontrol et
- Her topluluğun About sayfasını oku (ne sunduğunu anla)
- Classroom'a gir, modülleri tara

### 3. Modül Seçimi
- En değerli modülleri belirle (Bilal için: AI otomasyon, n8n, agentic sistemler, müşteri bulma)
- %0 tamamlanma olanlara özellikle bak (hiç girilmemiş, potansiyel yüksek)

### 4. İçerik Çekme
- Browser ile modüle tıkla
- Not: Skool React SPA'dır, buton onclick'leri HTML'de görünmez. Tıklama çalışmazsa Bilal'den URL atmasını iste
- Açılan sayfadaki ders başlıklarını, kaynakları ve içeriği oku

### 5. Skill Oluşturma
- Modüldeki en değerli bilgileri seç (cımbızla, nokta atışı)
- Hermes skill'i oluştur:
  - İçerik: özet, kod örnekleri, püf noktaları, referanslar
  - Ad: konuyu yansıtan kısa isim
  - Kategori: varsa mevcut umbrellaya ekle

### 6. Güvenlik
- Kullanıcı adı/şifre konuşma dışına çıkmaz
- Memory'e kaydedilmez
- Browser session'ı iş bitince kapat

## Digital Academy Modülleri (Değer Sırası)

| Modül | İlerleme | Değer | Açıklama |
|-------|----------|-------|----------|
| Agentic Sistemler | %0 | 🥇 | AI ajanları kur, bağla, otopilota al |
| n8n ile Kodsuz Otomasyon | %7 | 🥇 | Bilal'in zaten yaptığı işin profesyonel versiyonu |
| AI Ajansı Kurmak | %3 | 🥇 | Müşteri bulma, satış, gelir modeli |
| 6000+ Hazır Sistem | %0 | 🥇 | Hazır workflow'lar, kopyala-yapıştır |
| Claude Code | %4 | 🥈 | Zaten biliyor ama ek ipuçları |
| Vibe Coding | %91 | 🥈 | Neredeyse bitmiş |
| Claude | %13 | 🥉 | Başlangıç seviye |
| SaaS Modeli | %100 | ✅ Tamam | Geç notlar alınabilir |

## Sorun Giderme

- **Tıklama çalışmıyor**: Skool React SPA, onclick attribute'ları görünmez. Bilal'den URL atmasını iste
- **Oturum düşüyor**: Sayfa yenilendiğinde veya navigate edildiğinde oturum gidebilir. Yeniden login gerekir
- **API kapalı**: Skool'un GraphQL API'sine dışarıdan erişilemez, sadece browser içinden çalışır
