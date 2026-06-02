# AgencyOS — Mimari & Kullanım Kılavuzu

> AI ajansı operasyonlarını tek platformda birleştiren açık BYOK sistem.
> Edinildiği yer: Digital Academy / AI Ajansı Kurmak modülü (Skool)
> Uygulama: https://agencyos-app-88990.netlify.app/
> ✅ Giriş: ergeneonline@gmail.com / `ErgeneAI2025!` (27 May 2026'da açıldı)
> ✅ Onboarding tamamlandı: Ajans=ErgeneAI, Şehir=Bursa, Niche=Diş kliniği, Hedef=₺50.000/ay
> 🚧 STEP 2'de: 60-SECOND PROBE ekranı — site URL girilip JARVIS lead bulacak

## 8 Ana Bölüm

### 🗺️ MAP + JARVIS
- **MAP**: Google Maps üzerinden işletme bulma, haritada lead keşfi
- **JARVIS**: Sesli/yazılı AI asistan, 54 araç, 7 komut
  - Lead ara, lead ekle, lead bilgisi, pipeline durumu, proje özeti, not ekle, yardım
  - Komut örn: `/lead_bul "Bursa otel"`, `/pipeline`, `/projeler`

### 📊 SALES PIPELINE
- CRM kanban: New → Contacted → Booked → Won (ve Closed)
- Her lead: ad, iletişim, not, aşama, değer, son temas
- Drag-drop ile aşama değiştirme
- Lead ekleme formu (manuel veya JARVIS ile)

### 📋 DASHBOARD
- MRR (Monthly Recurring Revenue)
- Aktif proje sayısı
- Pipeline değeri (toplam lead değeri)
- Lead sayısı ve dağılımı
- Son aktiviteler (timeline)

### 🤖 ASSISTANT
- Serbest AI chat (Gemini arka uç)
- Herhangi bir konuda soru sor, fikir al
- Playbook'lardan alıntı yapabilir

### 📁 PROJECTS
- Proje workspace: her müşteri için ayrı alan
- Servis ekleme (örn: IG DM asistanı, web sitesi, chatbot)
- Görev yönetimi (todo list)
- Rapor oluşturma (PDF/HTML çıktı)

### 📖 PLAYBOOKS
- **20 Niche Playbook**: Hukuk, diş kliniği, emlak, e-ticaret, spor salonu, medikal estetik, restoran, oto galeri, influencer, gayrimenkul, fitness koçu, danışmanlık, psikoloji, kuaför, çocuk gelişimi, eğitim, lojistik, inşaat, otel, sigorta.
- **6 Formül**: Fiyatlandırma, teklif, onboarding, teslimat, upsell, retainer
- **10 Offer**: Paketlenmiş hizmet teklifleri (starter/pro/enterprise)
- **30 Case Study**: Gerçek müşteri hikayeleri ve sonuçlar
- **Proposal Yazma**: Otomatik teklif oluşturma (müşteri adı + ihtiyaç → doldurulmuş teklif)

### ⚙️ SETTINGS
- **Vault**: API key'leri (Gemini, OpenAI, n8n, Instagram, Telegram vb.)
- **Team**: Çalışan/ortak ekleme, rol bazlı yetki
- **Claude Code MCP**: Terminal'den AgencyOS yönetimi için MCP sunucusu (62 tool)
  - Lead CRUD, pipeline, proje, playbook, rapor
  - Kurulum: `npm install -g @agencyos/mcp` → Claude Code MCP settings'e ekle
- **Telegram Bot**: Cepten yönetim
  - Lead bildirimleri, pipeline güncelleme, hızlı not
  - `/lead`, `/pipeline`, `/proje`, `/rapor` komutları

### 🐘 Elephant
- Büyük resim: ajans vizyonu, hedefler, strateji
- Aylık/çeyreklik hedef takibi
- "Neredeyiz, nereye gidiyoruz?" kontrol paneli

## 9 Ders Sırası ve Süreleri

| # | Ders | Süre | Özet |
|---|------|------|------|
| 1 | AgencyOS Nedir + Kurulum | 4 dk | Platform tanıtımı, BYOK, 4 dk'da ayağa kaldırma |
| 2 | Arayüz Turu | ~10 dk | 8 bölümün gezilmesi |
| 3 | JARVIS AI Asistan | ~15 dk | 54 araç, 7 komut, sesli komut |
| 4 | Playbook'lar ve Proposal | ~20 dk | 20 niche şablonu, otomatik teklif |
| 5 | CRM + Sales Pipeline | ~15 dk | Lead yönetimi, kanban, takip |
| 6 | Proje Yönetimi | ~15 dk | Workspace, görev, rapor |
| 7 | Claude Code MCP | ~20 dk | 62 tool, terminal entegrasyonu |
| 8 | Telegram Bot | ~10 dk | Cep telefonundan yönetim |
| 9 | Gerçek İş Akışları | ~25 dk | Lead → Teklif → Proje → Teslimat akışı |

## Hesap & Onboarding Detayları

### İlk hesap (ergenebilal@gmail.com)
- "User already registered" çıktı — şifre unutuldu
- "Forgot password" → reset email gönderildi (kullanıcı mail'den yapacak)

### Yeni hesap (ergeneonline@gmail.com)
- **Email:** ergeneonline@gmail.com
- **Password:** ErgeneAI2025!
- **Name:** Bilal Ergene
- **Ajans:** ErgeneAI
- **Şehir:** Bursa
- **Hizmet:** AI otomasyon, chatbot, web tasarım, sosyal medya yönetimi
- **Niche:** Diş kliniği (onboarding'de seçilen ilk seçenek)
- **Hedef aylık gelir:** ₺50.000
- **27 Mayıs 2026'da kuruldu**

### STEP 2 — 60-SECOND PROBE (Onboarding devamı)
Onboarding'in 2. adımı soruyor: "Markanın URL'ini ver — JARVIS 60 saniyede Google Maps'ten 50 lead bulsun"
- Seçenek 1: 🎯 Müşteri bul (ürün satın alacak kişiler)
- Seçenek 2: 🤝 Partner ajans bul (resell/referral ajanslar)
- Buton: "JARVIS'i çalıştır 🚀"
- Buton: "Atla — sonra eklerim"
- ErgeneAI için site: https://aiergene.xyz

## Browser Tool Teknikleri (React Formlar İçin)

AgencyOS Netlify SPA olduğu için React state yönetimi kullanıyor. Browser tool ile form doldururken:

### Select dropdown seçimi
CDP `browser_click` genellikle select option elementlerinde "Could not compute box model" hatası verir.
**Çözüm:** JavaScript ile select elementine doğrudan değer ata ve event dispatch et:
```js
var sel = document.querySelector('select');
for (var i = 0; i < sel.options.length; i++) {
  if (sel.options[i].text === 'Bursa') {
    sel.selectedIndex = i;
    sel.dispatchEvent(new Event('change', {bubbles: true}));
    break;
  }
}
```

### Input alanlarını doldurma
`browser_type` çalışır ama kalabalık formlarda sayfa refresh/yönlendirme olursa kaybolabilir.
**React formlar için sağlam yöntem (JS native setter + events):**
```js
var nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
nativeSetter.call(inputElement, 'değer');
inputElement.dispatchEvent(new Event('input', {bubbles: true}));
inputElement.dispatchEvent(new Event('change', {bubbles: true}));
```

### Form submit
Buton referansı snapshot'ta trunk edilmişse JS ile bul:
```js
var btns = document.querySelectorAll('button');
btns.forEach(function(b) {
  if (b.textContent.includes('AJANSIMI KUR')) b.click();
});
```

## Kurulum Sonrası Yapılacaklar

1. Gemini API key gir (Vault'a)
2. Claude Code MCP kurulumu (npm ile)
3. Telegram Bot bağlantısı
4. STEP 2'yi tamamla — site URL'ini ver veya atla
5. İlk lead'i ekle (manuel veya MAP'ten)
6. Bir playbook seç ve proposal oluştur
7. Proje workspace aç (ör: IG DM Asistanı)
8. Dashboard'u kontrol et

## ErgeneAI İçin Uyarlama Notları

- **Playbook**: "Otel" ve "Genel İşletme" playbook'ları ErgeneAI'nin ana müşteri profiline uygun
- **IG DM Asistanı**: AgencyOS altında proje workspace olarak açılabilir
- **Lead kaynağı**: Instagram'dan gelen DM'ler manuel veya JARVIS ile pipeline'a eklenebilir
- **Telegram Bot**: Hermes'in mevcut Telegram altyapısına paralel veya entegre çalışabilir
- **KPI hedefleri**: Dashboard'da MRR, lead sayısı, dönüşüm oranı takip edilir
