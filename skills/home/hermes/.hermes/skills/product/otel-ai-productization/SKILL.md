---
name: otel-ai-productization
version: 1.0.0
author: Hermes
description: HKUDS/nanobot'u otellere satılabilir bir ürün haline getirme rehberi — ürünleştirme, satış, teslimat ve sonrası
---

# OtelAI Ürünleştirme & Satış Rehberi

## 1. Ön Hazırlık (1 saat)

### Sunucuda Yapılacaklar
- `/home/hermes/nanobot/` üzerinde çalış (HKUDS/nanobot v0.2.1 kurulu)
- `~/.nanobot/config.json` içinde otel bilgilerini yapılandır
  - Provider: DeepSeek
  - Channel: Telegram veya WhatsApp
  - Model: deepseek-v4-flash

### Markalama (Codex yapar)
- CLI'da "nanobot" yazısını "OtelAI" olarak değiştir
- WebUI'da logo ve renkleri otel markasına göre ayarla
- Mesaj template'lerinde otel adını kullan
- QR kod oluştur: `qrencode -o otel-qr.png "https://wa.me/905551234567"`

### Kanal Stratejisi
- **İlk müşteri için:** Telegram bot ile başla (sıfır kurulum, sıfır maliyet, 5 dk)
- **Sonraki müşteriler için:** WhatsApp Business API'ye geç
- Neden Telegram önce: Meta onay süreci beklemeden satışı kapat, referans oluştur
- WhatsApp'a geçiş: config'de 1 satır değişiklik, mevcut müşteri etkilenmez

### WhatsApp Kurulumu (Müşteri sayısı arttığında)
- Meta Business hesabı zaten var (Facebook App ID: 1699094787751073 — IG DM asistanından)
- WhatsApp ürünü Meta Business hesabına eklenmeli (henüz eklenmemiş)
- Yeni SIM kart gerek (otel adına, kişisel WhatsApp'ı çakıştırma)
- Onay süreci: 1-2 gün (Meta incelemesi)
- Maliyet: İlk 1.000 konuşma/ay ücretsiz, sonrası ~$0.005-0.05/konuşma
- 30 odalı otel için ayda ~100-300 konuşma = fatura çıkmaz
- Webhook: ücretsiz, mevcut n8n altyapısı kullanılabilir

### Müşteri Akışı (Kullanıcı Gözünden)
1. Müşteri odaya girer, masada QR kart görür: "Oda görevliniz WhatsApp'ta sizi bekliyor"
2. QR okutur → WhatsApp/Telegram açılır, otelin adı yazılı sohbet başlar
3. Müşteri sorar: "WiFi şifresi ne?" → 2 saniyede cevap gelir
4. Hiçbir şey yüklemeye, üye olmaya gerek yok

## 2. Otel Bilgileri (Müşteriden Alınır)

Müşteriye sorulacak sorular (basit bir form):
- Otel adı, adresi, telefon
- WiFi ağ adı ve şifresi
- Kahvaltı saatleri (açılış/kapanış)
- Havuz/spor salonu saatleri
- Oda tipleri ve fiyat aralıkları
- Restoran menüsü varsa (3-5 popüler yemek yeter)
- Çevrede gezilecek 3-5 yer
- Acil durum numarası (resepsiyon)
- Misafirlere hoş geldin mesajı

Bu bilgiler `~/.nanobot/config.json` içine "hotel" anahtarı altında kaydedilir.

## 3. Satış Konuşması (Bilal Yapar)

### Kullanılacak Cümleler:
- "Müşterileriniz odadan çıkmadan WhatsApp'tan size ulaşabiliyor"
- "Resepsiyonun yükünü 7/24 hafifletiyor"
- "Kurulum 1 saat, sonra hiçbir şey yapmanız gerekmiyor"
- "İlk ay ücretsiz deneyin, memnun kalmazsanız kaldırırım"

### İtiraz Cevapları:
- *"Teknoloji anlamam."* → "Hiçbir şey anlamanıza gerek yok. QR'ı basıp odaya koyuyorum, çalışıyor."
- *"Pahalı."* → "Ayda 2.500₺, bir garson maaşının 10'da 1'i. 7/24 çalışıyor. İlk ay ücretsiz deneyin."
- *"Müşteri sevmez."* → "Bugün herkes WhatsApp kullanıyor. Telefonla resepsiyonu aramaktan daha kolay."
- *"Zaten resepsiyon var."* → "Resepsiyon 7/24 aynı soruları cevaplamaktan tükeniyor. Bu sistem onların yükünü alır."

### Satış Adımları (Sıralı)
1. **Demo hazırla:** Telefonunda canlı bir otel asistanı göster. Müşterinin kendi otelinin ismi geçsin.
2. **Referans bul:** İlk oteli ücretsiz kur. "Deneyin, memnun kalırsanız devam ederiz." 1 hafta sonra referansın olur.
3. **Zincirle:** Aynı bölgedeki diğer otellere git: "Bak şu otel kullanıyor, çok memnun."
4. **Kapat ve unut:** Kurulum 1 saat, sonra aylık ödeme otomatik.

## 4. Teslimat Adımları

1. QR kodu bas (matbaa, 500 adet ~50₺)
2. QR'ı oda başına 1 tane olacak şekilde masaya/komodine koy
3. Test et: kendi telefonunla dene
4. Resepsiyona eğitim ver (2 dk): "Bak bu kadar, soruları gelince cevaplıyor"
5. Otel müdürüne demo yap

## 5. Fiyatlandırma

| Paket | Kurulum | Aylık | Kimin için |
|---|---|---|---|
| Basic | 5.000₺ | 1.000₺ | Butik otel (<30 oda) |
| Pro | 10.000₺ | 2.500₺ | Orta ölçek (30-100 oda) |
| Zincir | 25.000₺ | 5.000₺ | Zincir otel (100+ oda) |

İlk müşteriye **PRO paketini ücretsiz kur** (1 ay). Referans olarak kullan.

## 6. Satış Sonrası

- Ayda 1 kere kontrol: "Bir sorun var mı?" (2 dk mesaj)
- Otel raporunu otomatik gönder: kaç misafir konuştu, en çok ne soruldu
- Güncelleme gerektiğinde (ör: kahvaltı saati değişti) config güncelle

## 7. Ölçekleme

10 otel = ayda 25.000₺ pasif
50 otel = ayda 125.000₺ pasif
100 otel = ayda 250.000₺ pasif

Her yeni otel için kurulum süresi: 1 saat.

## Ek Kaynaklar

Bu skill'in altında aşağıdaki dosyalar bulunur:

### References
- `references/coo-crisis-framework.md` — Kriz karar çerçevesi, delege testi, finansal domino hesabı
- `references/nanobot-setup-notes.md` — HKUDS/nanobot kurulum, systemd servisi, lisans notları

### Templates
- `templates/fiyat-teklifi.md` — Müşteriye verilecek fiyat teklifi şablonu
