# Finansal Planlama Şablonu

ErgeneAI finansal durum değerlendirmesi ve çalışma programı çıkarma şablonu.

## Kullanım
Bu referans, kullanıcı mali durumunu değerlendirmek ve çalışma programı oluşturmak için kullanılır.

## Template Yapısı

### Mevcut Durum
```
### Bilinen Giderler
- Sunucu (Keyubu VPS): ~250 TL/ay
- API maliyetleri: [______]
- Diğer: [______]

### Bilinmeyen Giderler (DOLDURULACAK)
- Kira: [______]
- Faturalar: [______]
- Kredi/Kart: [______]
- Ulaşım: [______]
- Yemek/harçlık: [______]

### Gelirler
- Aktif iş: [______]
- Dijital satışlar: [______]

### Nakit
- Cepte/Banka: [______]
```

### Çalışma Programı (Günlük)
Kullanıcının mevcut cron'larına göre günlük akış. TR saati (UTC+3) kullan.

### Öncelikli Projeler
| # | Proje | Hedef | Süre | Durum |
|---|-------|-------|------|-------|
| 1 | [Proje adı] | [Hedef ₺] | [Süre] | [Aktif/Beklemede] |

### Kritik Hedefler (30 Gün)
- [ ] [Hedef 1]
- [ ] [Hedef 2]

## Kurallar
- Projeler "çekmecede" ise asla gündeme getirme
- Günlük finans kontrolü cron ile yapılır (TR 09:00)
- Sadece para getirecek aksiyonları raporla

---

## Kurye Geliri Planlama Patterni (Kanıtlanmış)

Bu pattern, kullanıcının esnaf kurye olarak çalıştığı dönemlerde finansal planlama için kullanılır.

### Finansal Veri Toplama Sırası

Kullanıcı finansal durum açtığında, şu sırayla bilgileri al/topla:

1. **Günlük kurye kazancı** — kaç paket, ne kadar TL, paket başı ortalama
2. **Haftalık çalışma günü sayısı** — kaç gün, hangi saatler
3. **Borçlar (vade sırasına göre):**
   - Kredi kartı (tutar, son ödeme, ticari mi değil mi → %25 asgari)
   - KMH (tutar, son ödeme)
   - KDV/vergi (tutar, aciliyet)
   - Sigorta ödemeleri (ne zaman bitiyor, yaklaşık tutar, karta çekilebilir mi)
4. **Ödeme döngüsü** — fatura ne zaman kesiliyor, para ne zaman yatıyor

### Hesaplama Mantığı

```python
# Örnek hesaplama (pseudo-code)
ortalama_paket_ucreti = toplam_kazanc / paket_sayisi
gunluk_hedef = minimum_alis  # kullanıcının koyduğu alt limit
haftalık_potansiyel = gun_sayisi * gunluk_hedef
aylık_potansiyel = haftalık_potansiyel * 4

# Borç yönetimi
asgari_kart = kart_borcu * 0.25  # ticari kart ise %25
kalan_nakit = hesaba_yatan - (asgari_kart + kmh_odemesi + yasam_masrafi)
```

### Nakit Akışı Takvimi

| Tarih | Olay | Nakit Etkisi |
|-------|------|--------------|
| Pazartesi | Fatura kesilir | - |
| Çarşamba | Para yatar (önceki haftanın) | +X₺ |
| Ayın 11'i | Kredi kartı son ödeme | -asgari veya tam |
| Ayın 14-15'i | KMH son ödeme | -KMH |
| Sigorta bitişi | Sigorta yenileme | karta çek → nakit 0₺ |

### Öncelik Sırası (Hangi Borç Önce)

1. **Motor sigortası** — motor olmazsa gelir olmaz. Karta çekilebiliyorsa çek.
2. **Kredi kartı asgarisi** — en azından asgari ödenmeli, yoksa kara listedesin.
3. **KMH** — yüksek faizli borç, hemen kapat.
4. **Vergi/KDV** — gecikme faizi düşük, en son.

### Kurye + AI Gelir Modeli

Kullanıcı "sen yükümü al, ben motordayken sen çalış" dediğinde:

| Gelir Kaynağı | Kim Yapar | Süre |
|---------------|-----------|------|
| Motor kuryelik | Kullanıcı (11:00-20:00) | ~9 saat/gün |
| AI müşteri lead toplama | AI asistan (sen motordayken) | Otomatik |
| AI teklif/satış hazırlığı | AI asistan | Önceden |
| AI müşteri görüşmesi | Kullanıcı (08:30-09:15) | ~45 dk/gün |

**Anahtar denklem:** 1 AI müşterisi (~4.500₺) = 1.5 gün motor mesaisi (~3.000₺). AI müşterileri kuryeye ek, alternatif değil.

### Günlük Akış (Kurye Haftası)

| Saat | Ne |
|------|----|
| 07:00-07:30 | Uyan, laptop'ı al, çık |
| 07:30-08:10 | Yürüyüş |
| 08:10-08:30 | Kahve + laptop aç |
| 08:30-09:15 | 🤝 AI seansı: lead incele + onayla |
| 09:15-09:45 | Eve dön, laptop bırak |
| 09:45-10:30 | Motor hazırlık |
| 11:00-20:00+ | 🏍️ Motor (3.000₺ altı eve yok) |

### Uyarılar

- **Ticari kredi kartı** → asgari %25, normal kart %30-40. Bunu kontrol et, plana yansıt.
- **Sigorta bitiş tarihi** kritik — motor olmazsa 0 gelir. Sigortayı mümkünse karta çek.
- **Açık sigorta dosyası** — kaza dosyası kapanmamışsa sigorta çok yüksek çıkar. Önce dosyayı kapattır.
