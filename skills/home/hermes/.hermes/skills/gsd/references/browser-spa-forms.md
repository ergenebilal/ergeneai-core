# Browser + React SPA Form Doldurma Tekniği

## Sorun
`browser_type` ile React tabanlı form alanlarına yazı yazmak çalışır (input/change event'lerini tetikler), ancak:
- `browser_click` ile `<select>` dropdown option'larına tıklamak **"CDP error (DOM.getBoxModel): Could not compute box model"** hatası verir
- JavaScript ile `el.value = '...'` set etmek React state'ini güncellemez (framework event chain'ini tetiklemez)

## Çözüm: JavaScript ile Native Setter + Event Dispatch

Dropdown seçimi ve input değerleri için **native value setter + event dispatch** kombinasyonu kullan:

```javascript
// INPUT için
var nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
nativeSetter.call(el, 'değer');
el.dispatchEvent(new Event('input', {bubbles: true}));
el.dispatchEvent(new Event('change', {bubbles: true}));

// TEXTAREA için  
var nativeSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
nativeSetter.call(el, 'değer');
el.dispatchEvent(new Event('input', {bubbles: true}));
el.dispatchEvent(new Event('change', {bubbles: true}));

// SELECT için
el.selectedIndex = uygunIndex;
el.dispatchEvent(new Event('change', {bubbles: true}));
```

## Doğrulama
```javascript
var allF = document.querySelectorAll('input, select, textarea');
var res = [];
allF.forEach(function(el) {
  var lbl = el.placeholder || el.name || 'select';
  res.push(lbl + ': ' + el.value);
});
res.join(' | ');
```

## Neden browser_type yetmedi?
- `<select>` option elementleri görünür DOM'da ama Playwright/Chrome DevTools Protocol onların bounding box'ını hesaplayamıyor (çünkü popup menu geçici olarak render ediliyor)
- `browser_type` + Enter dropdown'a yazılan metni submit ediyor ama React state'ini güncellemiyor

## Ne Zaman Kullan
- React, Vue, Angular gibi SPA framework'leriyle çalışan formlar
- Özel dropdown/combobox component'leri (shadcn/ui, Material UI, Chakra UI)
- Normal HTML formlar için `browser_type` yeterli

## SPA Session Loss (AgencyOS Pattern)
Bazı SPA'lar (özellikle Netlify-deployed JAMstack) her `browser_navigate` çağrısında **auth state'i kaybeder** — localStorage/sessionStorage'daki token temizlenir ve login ekranına düşersin. Çözüm:
- Mümkünse sayfalar arası gezinmek için `browser_navigate` kullanma — SPA kendi iç routing'ini kullanır
- SPA'nın butonlarına tıkla (`browser_click`) ve state değişimini bekle
- Zorunlu `browser_navigate` sonrası: yeniden login yap (email + şifre)
- Auth token'ı JS ile okuyup navigate sonrası geri yazmak da bir seçenek

## Tutorial/Onboarding Overlay Kilidi
Bazı SPA'lar onboarding tutorial'ı sidebar navigasyonunun üzerine bindirir:
- Tutorial kapatılmadan sidebar butonları (Knowledge, Playbooks, Settings) devre dışı kalır
- Çözüm: Önce tutorial'ı kapat (Skip tutorial / ✕ butonu), sonra navigasyon dene
- Tutorial butonlarını bulmak için `document.querySelectorAll('button')` ile tüm butonları tara

## Vault/API Key Management (AgencyOS Deseni)
API key ekleme akışı:
1. Settings > Vault sekmesine git (sidebar'daki Vault butonu veya Vault'a git kısayolu)
2. İlgili servisin "+ EKLE" butonuna tıkla — input alanı açar
3. Key'i `Object.getOwnPropertyDescriptor` native setter + event dispatch ile yaz
4. Aynı "+ EKLE" butonuna tekrar tıkla (toggle — input varken save yapar)
5. "AKTIF" / "✓ Kaydedildi" onayını kontrol et
6. Input alanı kapanır ve key maskelenir (••••••••)
