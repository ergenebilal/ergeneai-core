---
name: financial-triage
description: "Personal finance triage, debt management, cash flow planning, and life coaching — for users in financial distress who need a structured plan across financial, mental, and physical fronts."
version: 1.0.0
author: Hermes Agent
tags: [finance, debt, coaching, personal, productivity, turkish]
---

# Financial Triage & Life Coaching

Use this skill when the user describes financial distress, debt problems, cash flow issues, or a desire to restructure their life finances. Covers **individual/personal** financial triage for self-employed, freelance, or gig-economy users.

## Phase 1: Data Collection

Get these numbers before making any recommendation:

**BORÇLAR:** Kredi kartı (tutar + ödeme tarihi), KMH/kredili mevduat (EN KRİTİK — günlük faiz), kredi, vergi/SSK, şahsi borçlar.

**GELİRLER:** Haftalık/aylık düzenli (son 3 ay ortalaması), proje/yan gelirler, AI işleri.

**GİDERLER (aylık):** Kira, fatura, ulaşım/yakıt, muhasebe, kart taksitleri, yeme içme (günlük × 30), sigara/alkol (dürüstçe sor), diğer.

**ANLIK NAKİT**

## Phase 2: Borç Öncelik Sırası

| Öncelik | Borç | Neden |
|---|---|---|
| 1 | KMH | Günlük faiz — en tehlikeli |
| 2 | Kredi kartı | Aylık faiz, min. ödeme tuzağı |
| 3 | Şahsi borç | İlişki riski |
| 4 | Kredi | Sabit taksit |
| 5 | Vergi | Yapılandırma mümkün |

**Kısır döngü:** Gelir belirsiz → nakit biter → karta yüklen → ödeme günü düşür → nakit biter → tekrar. Kırılma: KMH'leri kapat, faiz yükünü sıfırla.

## Phase 3: Multi-Front Strategy (EN ÖNEMLİ İÇGÖRÜ)

Üç cephe birbirini besler. Para planı yetmez — mental/fiziksel blokerları da ele al:

- **💰 MALİ:** Borç planı, gelir artışı
- **🧠 MENTAL:** Özgüven, yalnızlık, anlam arayışı
- **🏃 FİZİKSEL:** Sağlık, alışkanlık, görünüm

Yukarı döngü: Sabah yürüyüşü → özgüven → az alkol (para cebinde kalır) → AI işlerinde üretim → para → daha iyi hissetme → yukarı döngü.

## Phase 4: Cash Flow

1. KMH'leri kapat (mevcut nakitle)
2. Yeme içme giderini günlük 400→250 TL'ye çek (ayda ~4.500 TL fark)
3. Yakıtı minimize et (iş dışı kullanım sıfır)
4. İlk ödemeyle YK KMH'yi kapat
5. 1-2 ay sıkı toparlanma

## Phase 5: Gelir Planı (AI Projeleri)

- Önce mevcut ürünleri envanterle
- 30 gün içinde ilk 5.000 TL hedefi
- Abonelik modeli (₺1.500/₺3.000/₺5.000)
- Satış kanalı netleştir

## Kullanıcıya Özel Notlar

## Linked Files

- `references/hesap-kitap-sablonu.md` — "Hesap kitap yapalım" dediğinde kullanılacak yapılandırılmış şablon. Anlık nakit, gelir/gider, borç öncelik sırası, 30 günlük hamleler.

Bu skill ErgeneAI (Bilal) bağlamında geliştirildi. Ana özellikler:
- Kısa, direkt Türkçe yanıt ister
- Önce mevcut credential'ları kontrol et
- DeepSeek V4 Flash tercih eder
- Öğleden sonra check-in bekler
- Denetim programını takip et, hatırlat
- Mental/fiziksel/mali ayrılmaz bütün

## References

- `references/hesap-kitap-sablonu.md` — Kullanıcı "hesap kitap yapalım" dediğinde izlenecek yapı. Anlık nakit pozisyonu, gelir/gider dengesi, 30 günlük hızlı kazanç hamleleri.

## Pitfalls

- ❌ **Yeni servis/abonelik/hesap ÖNERME.** Nakit sıkışıklığındaki kullanıcıya Brevo, Canva Pro, yeni API key vs. önerme. Önce mevcutta ne var kontrol et (n8n credential list, Google, OpenAI, Telegram).
- ❌ **Ücretli araç önerme.** Bedava alternatif yoksa bile önerme — kullanıcının zaten bildiği bir ücretli aracı sorabilirsin ama sen önerme.
- ❌ "Spor salonuna git" deme — evde 20 dk yürüyüş de
- ❌ "Alkolü bırak" deme — "evde yalnız içme" de
- ❌ Borç takibini her konuşmada güncelle
- ❌ Finansal/metal/fiziksel ayrı ele alınmaz
- ❌ **Python modül adı çakışması** — `calendar.py`, `test.py`, `time.py` gibi dosya adları stdlib modüllerini ezer. `sys.path.insert(0, user_dir)` yapıyorsan önce stdlib import et (cache'e al), sonra path ekle. Finans script'lerinde sık karşılaşılır.
- ❌ **Kritik tarihleri elle hatırlama** — Kritik tarihler (ödeme, sigorta bitiş) için `kritik_uyari.py` script'i var, ona güven. Elle "14 gün kaldı" hesaplama yapma, script otomatik uyarır.
