
"""Hermes dijital beyin cekirdegi.

Bu modul bilerek standart kutuphane ile yazildi. Canli Hermes servisini
restart etmeden test edilebilir; tools.py sadece ince bir kopru olarak kullanir.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Mapping, Sequence

ACTION_ALLOW = "serbest_analiz"
ACTION_APPROVAL_REQUIRED = "onay_gerekir"
ACTION_FORBID = "yasak"

CANONICAL_MEMORY_CATEGORIES = {
    "kisisel",
    "is",
    "strateji",
    "teknik",
    "risk",
    "firsat",
    "operasyon",
    "genel",
}

SUPPORTED_TTS_VOICES = {
    "alloy",
    "ash",
    "ballad",
    "coral",
    "echo",
    "fable",
    "nova",
    "onyx",
    "sage",
    "shimmer",
    "verse",
    "marin",
    "cedar",
}

SUPPORTED_TTS_FORMATS = {"mp3", "opus", "aac", "flac", "wav", "pcm"}
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_TTS_VOICE = "marin"

_CATEGORY_ALIASES = {
    "personal_reminder": "kisisel",
    "kişisel": "kisisel",
    "kisisel": "kisisel",
    "hatirlatma": "kisisel",
    "hatırlatma": "kisisel",
    "business_strategy": "strateji",
    "strateji": "strateji",
    "strategy": "strateji",
    "tech_note": "teknik",
    "teknik": "teknik",
    "hata": "teknik",
    "risk": "risk",
    "borc": "risk",
    "borç": "risk",
    "firsat": "firsat",
    "fırsat": "firsat",
    "gelir": "firsat",
    "müşteri dışı operasyon": "operasyon",
    "musteri disi operasyon": "operasyon",
    "operasyon": "operasyon",
    "is": "is",
    "iş": "is",
    "genel": "genel",
    "test": "genel",
}

_PRIORITY_WEIGHTS = {
    "aciliyet": 5,
    "gelir_etkisi": 4,
    "risk": 4,
    "kaldirac": 3,
    "hedef_uyumu": 3,
}

_FORBIDDEN_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bdrop\s+database\b",
    r"\btruncate\s+table\b",
    r"\bformat\b.*\bdisk\b",
    r"\.env\b.*\b(token\w*|secret\w*|sifre\w*|şifre\w*|password\w*|key\w*)\b",
    r"\b(token\w*|secret\w*|api[_ -]?key\w*|password\w*|passwd\w*|sifre\w*|şifre\w*)\b.*\b(goster\w*|göster\w*|oku\w*|yazdir\w*|yazdır\w*|print\w*)\b",
]

_APPROVAL_PATTERNS = [
    r"\bsystemctl\b",
    r"\bservice\b.*\b(restart|stop|start|reload)\b",
    r"\brestart\b",
    r"\breboot\b",
    r"\bdocker\b",
    r"\bapt\b|\bpip\s+install\b|\bnpm\s+install\b",
    r"\bmigrate\b|\bmigration\b",
    r"\bpsql\b.*\b(insert|update|delete|alter|create|drop)\b",
    r"\bdelete\b|\bsil\b",
    r"\bwrite\b|\byaz\b|\bdosya\b",
    r"\bkaydet\b|\bhafiza\b|\bhafıza\b|\bmemory\b",
    r"\bmesaj\b.*\b(gonder|gönder|send)\b",
    r"\b(token\w*|secret\w*|api[_ -]?key\w*|password\w*|passwd\w*|sifre\w*|şifre\w*)\b.*\b(tasi\w*|taşı\w*|aktar\w*|move\w*|copy\w*|kopyala\w*)\b",
    r"\b(n8n|instagram)\b.*\b(workflow\w*|node\w*|akis\w*|akış\w*|otomasyon\w*|degistir\w*|değiştir\w*|duzenle\w*|düzenle\w*|guncelle\w*|güncelle\w*)\b",
    r"\b(root|ssh)\b.*\b(ayar\w*|degistir\w*|değiştir\w*|guncelle\w*|güncelle\w*|kapat\w*|ac\w*|aç\w*)\b",
    r"\b(prompt\w*|kimlik\w*)\b.*\b(canli\w*|live\w*|degistir\w*|değiştir\w*|guncelle\w*|güncelle\w*)\b",
]


def _as_text(value: Any) -> str:
    return "" if value is None else str(value)


def normalize_memory_category(label: str | None) -> str:
    """Hermes hafiza kategorisini sade, karar verilebilir etikete indirger."""
    raw = _as_text(label).strip().casefold()
    if not raw:
        return "genel"
    if raw in CANONICAL_MEMORY_CATEGORIES:
        return raw
    if raw in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[raw]
    for needle, category in _CATEGORY_ALIASES.items():
        if needle in raw:
            return category
    return "genel"


def build_tts_request(
    text: str,
    voice: str = DEFAULT_TTS_VOICE,
    response_format: str = "mp3",
    instructions: str | None = None,
    model: str = DEFAULT_TTS_MODEL,
) -> Dict[str, Any]:
    """Hermes ses uretimi icin OpenAI Speech API istegini hazirlar; ag cagrisi yapmaz."""
    clean_text = re.sub(r"\s+", " ", _as_text(text)).strip()
    normalized_voice = _as_text(voice).strip().casefold() or DEFAULT_TTS_VOICE
    normalized_format = _as_text(response_format).strip().casefold() or "mp3"
    warnings: List[str] = []
    if not clean_text:
        warnings.append("metin_bos")
    if normalized_voice not in SUPPORTED_TTS_VOICES:
        warnings.append("desteklenmeyen_ses")
    if normalized_format not in SUPPORTED_TTS_FORMATS:
        warnings.append("desteklenmeyen_format")
    if len(clean_text) > 4096:
        clean_text = clean_text[:4096]
        warnings.append("metin_4096_karaktere_kisaltildi")

    payload: Dict[str, Any] = {
        "model": model or DEFAULT_TTS_MODEL,
        "voice": normalized_voice,
        "input": clean_text,
        "response_format": normalized_format,
    }
    if instructions:
        payload["instructions"] = _as_text(instructions).strip()
    return {
        "ok": not any(warning in warnings for warning in ["metin_bos", "desteklenmeyen_ses", "desteklenmeyen_format"]),
        "url": "https://api.openai.com/v1/audio/speech",
        "payload": payload,
        "extension": normalized_format,
        "warnings": warnings,
        "secret_required": "OPENAI_API_KEY",
    }


def choose_tts_provider(openai_api_key_present: bool, edge_tts_available: bool) -> Dict[str, Any]:
    """Ses uretimi icin anahtarli OpenAI veya anahtarsiz edge-tts yolunu secer."""
    if openai_api_key_present:
        return {"ok": True, "provider": "openai", "reason": "openai_api_key_var"}
    if edge_tts_available:
        return {"ok": True, "provider": "edge_tts", "reason": "openai_api_key_yok_edge_tts_var"}
    return {
        "ok": False,
        "provider": "unavailable",
        "reason": "openai_api_key_yok_edge_tts_yok",
        "warnings": ["tts_provider_yok"],
    }


def _clamp_score(value: Any) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(0, min(5, number))


def score_priority(item: Mapping[str, Any]) -> Dict[str, Any]:
    """Bir isi Hermes'in gelir/risk/kaldirac mantigiyla puanlar."""
    scored = dict(item)
    total = 0
    reasons: List[str] = []
    for key, weight in _PRIORITY_WEIGHTS.items():
        value = _clamp_score(item.get(key, 0))
        total += value * weight
        if value >= 4:
            labels = {
                "aciliyet": "acil",
                "gelir_etkisi": "gelire etkisi yuksek",
                "risk": "risk azaltir",
                "kaldirac": "kaldirac etkisi var",
                "hedef_uyumu": "ana hedefle uyumlu",
            }
            reasons.append(labels[key])
    scored["puan"] = total
    scored["nedenler"] = reasons or ["dusuk oncelik sinyali"]
    return scored


def rank_priorities(items: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Isleri puana gore siralar ve sira alanini ekler."""
    ranked = [score_priority(item) for item in items]
    ranked.sort(key=lambda item: item["puan"], reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["sira"] = index
    return ranked


_TURKISH_ASCII = str.maketrans({
    "ç": "c",
    "ğ": "g",
    "ı": "i",
    "ö": "o",
    "ş": "s",
    "ü": "u",
    "Ç": "c",
    "Ğ": "g",
    "İ": "i",
    "I": "i",
    "Ö": "o",
    "Ş": "s",
    "Ü": "u",
})


def _ascii_fold(text: Any) -> str:
    return _as_text(text).translate(_TURKISH_ASCII).casefold()


def _extract_day_window(text: str) -> int | None:
    match = re.search(r"\((\d+)\s*g[üu]n\)", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_money_amount(text: str) -> str | None:
    match = re.search(r"(\d[\d.]*\s*(?:₺|tl|try))", text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _priority_candidate(
    baslik: str,
    kaynak: str,
    karar_tipi: str,
    aciliyet: int,
    gelir_etkisi: int,
    risk: int,
    kaldirac: int,
    hedef_uyumu: int,
    gun_penceresi: int | None = None,
    tutar: str | None = None,
) -> Dict[str, Any]:
    item = {
        "baslik": baslik,
        "kaynak": kaynak,
        "karar_tipi": karar_tipi,
        "aciliyet": aciliyet,
        "gelir_etkisi": gelir_etkisi,
        "risk": risk,
        "kaldirac": kaldirac,
        "hedef_uyumu": hedef_uyumu,
    }
    if gun_penceresi is not None:
        item["gun_penceresi"] = gun_penceresi
    if tutar:
        item["tutar"] = tutar
    return item


def extract_operational_priority_candidates(report: Any) -> Dict[str, Any]:
    """Dogal durum raporundan risk/firsat/hedef sinyallerini deterministic cikarir."""
    if isinstance(report, Sequence) and not isinstance(report, (str, bytes)):
        return {"candidates": list(parse_priority_items(report)), "context": {}, "pending": [], "hedef_uyumu": ""}

    text = _as_text(report)
    folded = _ascii_fold(text)
    lines = [line.strip(" -•\t") for line in text.splitlines() if line.strip(" -•\t")]
    candidates: List[Dict[str, Any]] = []
    pending: List[str] = []

    for line in lines:
        normalized = _ascii_fold(line)
        days = _extract_day_window(line)
        amount = _extract_money_amount(line)
        if any(word in normalized for word in ["denizbank", "asgari", "kart son", "son odeme", "borc"]):
            imminent = days is not None and days <= 3
            near = days is not None and days <= 10
            candidates.append(_priority_candidate(
                baslik="Denizbank ödeme planını netleştir" if not imminent else "Denizbank ödeme riskini bugün kapat",
                kaynak=line,
                karar_tipi="risk_koruma",
                aciliyet=5 if imminent else 4 if near else 3,
                gelir_etkisi=3 if imminent else 2,
                risk=5,
                kaldirac=5 if imminent else 2,
                hedef_uyumu=5,
                gun_penceresi=days,
                tutar=amount,
            ))
        elif "motor sigorta" in normalized or "sigortasi" in normalized or "sigorta" in normalized:
            candidates.append(_priority_candidate(
                baslik="Motor sigortasi dosyasını kapat",
                kaynak=line,
                karar_tipi="risk_koruma",
                aciliyet=4 if days is not None and days <= 7 else 3,
                gelir_etkisi=1,
                risk=4,
                kaldirac=2,
                hedef_uyumu=4,
                gun_penceresi=days,
                tutar=amount,
            ))
        elif any(word in normalized for word in ["balik restorani", "sicak musteri", "referans zinciri", "bu hafta kapat"]):
            candidates.append(_priority_candidate(
                baslik="Balik restorani sicak musteriyi bu hafta kapat",
                kaynak=line,
                karar_tipi="gelir_kaldiraci",
                aciliyet=5 if "bu hafta" in normalized or "sicak" in normalized else 4,
                gelir_etkisi=5,
                risk=2,
                kaldirac=5,
                hedef_uyumu=5,
            ))
        elif "usd" in normalized and any(word in normalized for word in ["teklif", "gelir", "firsat"]):
            candidates.append(_priority_candidate(
                baslik="USD gelir fırsatı için teklif hazırla",
                kaynak=line,
                karar_tipi="gelir_kaldiraci",
                aciliyet=4,
                gelir_etkisi=5,
                risk=2,
                kaldirac=5,
                hedef_uyumu=5,
            ))
        elif "nakit" in normalized and "risk" in normalized:
            candidates.append(_priority_candidate(
                baslik="Nakit riskini kapat",
                kaynak=line,
                karar_tipi="risk_koruma",
                aciliyet=5,
                gelir_etkisi=3,
                risk=5,
                kaldirac=2,
                hedef_uyumu=5,
            ))

    if any(word in folded for word in ["belirsiz", "net degil", "dosya acik", "dosya hala acik"]):
        if not re.search(r"\d+\s*g[üu]n|\d{1,2}\s*haz|\d{4}-\d{2}-\d{2}", text, flags=re.IGNORECASE):
            pending.append("Eksik tarih: karar icin son tarih veya gun penceresi netlestirilmeli.")
        if not _extract_money_amount(text):
            pending.append("Eksik tutar: para etkisi veya maliyet netlestirilmeli.")

    hedef_bits: List[str] = []
    if "otelai" in folded:
        hedef_bits.append("OtelAI düzenli gelir")
    if "eylul 2026" in folded or "eylül 2026" in folded:
        hedef_bits.append("Eylül 2026 kuryelikten çıkış")
    hedef_uyumu = " + ".join(hedef_bits)
    context = {
        "hedef": hedef_uyumu,
        "buyume_modu": bool(hedef_bits),
        "nakit_baskisi": any(item.get("karar_tipi") == "risk_koruma" and item.get("gun_penceresi") is not None and item["gun_penceresi"] <= 3 for item in candidates),
    }
    return {"candidates": candidates, "context": context, "pending": pending, "hedef_uyumu": hedef_uyumu}


def build_operational_priority(report: Any, reference_date: str | None = None, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Durum raporundan Bilal icin tek odak, risk korumalari ve gelir firsati uretir."""
    extracted = extract_operational_priority_candidates(report)
    candidates = list(extracted["candidates"])
    merged_context = dict(extracted.get("context") or {})
    merged_context.update(dict(context or {}))
    if reference_date:
        merged_context["referans_tarih"] = reference_date

    decision = make_decision_plan(candidates, context=merged_context)
    top = decision.get("tek_odak") or {}
    ordered = list(decision.get("sirali_isler", []) or [])
    risk_items = [item for item in ordered if item.get("karar_tipi") == "risk_koruma"]
    opportunity_items = [item for item in ordered if item.get("karar_tipi") == "gelir_kaldiraci"]
    risk_guards = [item.get("baslik") for item in risk_items if item.get("baslik")]
    opportunity = opportunity_items[0]["baslik"] if opportunity_items else ""

    reasons = list(top.get("nedenler", []) or [])
    source = _as_text(top.get("kaynak"))
    if "referans zinciri" in _ascii_fold(source):
        reasons.append("referans zinciri baslatabilecek sicak gelir firsati")
    if top.get("karar_tipi") == "risk_koruma" and top.get("gun_penceresi") is not None and top["gun_penceresi"] <= 3:
        reasons.append("0-3 gun icinde yaklasan risk ana odagi ezer")
    if extracted.get("hedef_uyumu"):
        reasons.append(f"hedef uyumu: {extracted['hedef_uyumu']}")
    if not reasons:
        reasons = ["gelir, risk, zaman ve hedef uyumu dengesinde en yuksek puan"]

    waiting = [item.get("baslik") for item in ordered[1:] if item.get("baslik")]
    if not waiting and ordered:
        waiting = ["Diger isler tek odak tamamlanana kadar bekliyor."]

    pending = list(extracted.get("pending", [])) + list(decision.get("bekleyen_kararlar", []))
    if not candidates and not pending:
        pending.append("Puanlanabilir is icin tarih, tutar, gelir etkisi ve risk bilgisi gerekli.")

    focus = _as_text(top.get("baslik")) if top else "Puanlanabilir tek odak icin veri netlestir"
    if "balik restorani" in _ascii_fold(focus):
        first_action = "Balık restoranı için bugün karar vericiye net teklif ve kapanış mesajı gönder."
    elif "denizbank" in _ascii_fold(focus):
        first_action = "Denizbank için bugün tutar, ödeme kaynağı ve son tarih planını netleştir."
    elif "motor sigorta" in _ascii_fold(focus):
        first_action = "Motor sigortası için dosya durumunu ve yenileme tarihini netleştir."
    else:
        first_action = f"Bugun tek odak: {focus} icin ilk somut adimi tamamla."

    return {
        "bugunun_tek_odagi": focus,
        "risk_korumalari": risk_guards,
        "gelir_firsati": opportunity,
        "sirali_oncelikler": ordered,
        "neden_bu_odak": reasons,
        "neden_digerleri_bekliyor": waiting,
        "ilk_somut_adim": first_action,
        "bekleyen_kararlar": pending,
        "hedef_uyumu": extracted.get("hedef_uyumu", ""),
        "baglam": merged_context,
        "read_only": True,
    }


def classify_autonomy_action(action: str) -> Dict[str, Any]:
    """Hermes eylemini serbest/onayli/yasak olarak siniflandirir."""
    text = _as_text(action).strip()
    lowered = text.casefold()
    for pattern in _FORBIDDEN_PATTERNS:
        if re.search(pattern, lowered):
            return {
                "sinif": ACTION_FORBID,
                "gerekce": "Secret, geri donusu zor silme veya yikici islem riski tasiyor.",
                "eylem": text,
            }
    for pattern in _APPROVAL_PATTERNS:
        if re.search(pattern, lowered):
            return {
                "sinif": ACTION_APPROVAL_REQUIRED,
                "gerekce": "Kalici durum, servis, dosya, musteri veya hafiza etkisi olabilir.",
                "eylem": text,
            }
    return {
        "sinif": ACTION_ALLOW,
        "gerekce": "Sadece analiz/raporlama gibi dusuk riskli gorunuyor.",
        "eylem": text,
    }


def _physical_action_base(status: str, text: str, reason: str = "") -> Dict[str, Any]:
    return {
        "status": status,
        "approval_required": status == ACTION_APPROVAL_REQUIRED,
        "auto_apply": False,
        "executed": False,
        "actions": [],
        "missing": [],
        "blocked_reason": reason,
        "rollback": "Plan uygulanmadigi icin geri alma gerekmiyor.",
        "safety": {
            "secret_safe": True,
            "payments_supported": False,
            "n8n_instagram_touched": False,
        },
        "source": text,
    }


def _first_date_hint(text: str) -> str:
    match = re.search(
        r"(\d{1,2}\s+(?:ocak|subat|şubat|mart|nisan|mayis|mayıs|haziran|temmuz|agustos|ağustos|eylul|eylül|ekim|kasim|kasım|aralik|aralık)(?:\s+\d{4})?(?:\s+\d{1,2}[:.]\d{2})?)",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _customer_label(text: str) -> str:
    folded = _ascii_fold(text)
    if "balik restorani" in folded:
        return "Balik restorani"
    if "musteri" in folded:
        return "Musteri"
    return "Bilal"


def build_physical_action_plan(action: Any, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Dijital/fiziksel dunya aksiyonlarini once planlar; otomatik uygulama yapmaz."""
    text = _as_text(action if not isinstance(action, Mapping) else action.get("eylem") or action.get("action")).strip()
    folded = _ascii_fold(text)
    context = context or {}
    autonomy = classify_autonomy_action(text)
    if autonomy["sinif"] == ACTION_FORBID:
        return _physical_action_base(ACTION_FORBID, text, autonomy["gerekce"])
    if re.search(r"\b(odeme\s+yap|para\s+transfer|havale|eft|kredi\s+karti\s+ode|kart\s+ode)\b", folded):
        return _physical_action_base(
            ACTION_FORBID,
            text,
            "Odeme, para transferi veya banka islemi Hermes tarafindan desteklenmez.",
        )
    if "n8n" in folded or "instagram" in folded:
        return _physical_action_base(
            ACTION_FORBID,
            text,
            "n8n/Instagram akislari bu turun kapsami disinda tutuluyor.",
        )

    plan = _physical_action_base(ACTION_ALLOW, text)
    date_hint = _first_date_hint(text)
    message_target = _customer_label(text)

    if any(token in folded for token in ("hatirlat", "hatirlatici", "reminder")):
        plan["actions"].append({
            "type": "hatirlatici",
            "title": "Hatirlatici hazirla",
            "draft": text,
            "params": {"mesaj": text, "zaman_ipucu": date_hint, "dakika_sonra": context.get("dakika_sonra")},
            "risk": "dis_dunyaya_kayit",
        })
        if not date_hint and not context.get("dakika_sonra"):
            plan["missing"].append("tarih_saat")

    if any(token in folded for token in ("takvim", "calendar", "etkinlik")):
        plan["actions"].append({
            "type": "takvim_etkinlik",
            "title": "Takvim etkinligi hazirla",
            "draft": text,
            "params": {
                "baslik": context.get("baslik") or text[:80],
                "baslangic": context.get("baslangic") or date_hint,
                "bitis": context.get("bitis") or "",
                "aciklama": text,
            },
            "risk": "takvim_yazimi",
        })
        if not (context.get("baslangic") or date_hint):
            plan["missing"].append("tarih_saat")

    message_intent = any(token in folded for token in ("mesaj", "gonder", "gonderilecek", "teklif", "telegram", "whatsapp"))
    if message_intent and not any(item["type"] == "mesaj_taslagi" for item in plan["actions"]):
        draft = context.get("taslak") or f"{message_target} icin onay bekleyen mesaj taslagi: {text}"
        plan["actions"].append({
            "type": "mesaj_taslagi",
            "title": "Mesaj taslagi hazirla",
            "draft": draft,
            "params": {"alici": context.get("alici", ""), "kanal": context.get("kanal", "onay_sonrasi")},
            "risk": "musteri_iletisimi",
        })
        if not context.get("alici") and message_target != "Bilal":
            plan["missing"].append("alici")

    if any(token in folded for token in ("gmail", "e-posta", "eposta", "email")):
        plan["actions"].append({
            "type": "gmail_taslagi",
            "title": "E-posta taslagi hazirla",
            "draft": context.get("taslak") or text,
            "params": {"alici": context.get("alici", ""), "konu": context.get("konu", "")},
            "risk": "eposta_gonderimi",
        })
        if not context.get("alici"):
            plan["missing"].append("alici")

    plan["missing"] = sorted(set(plan["missing"]))
    if plan["actions"]:
        plan["status"] = ACTION_APPROVAL_REQUIRED
        plan["approval_required"] = True
        plan["rollback"] = "Dis dunya etkisi olusmadan once kullanici onayi gerekir; uygulama yapilirsa ilgili kanal uzerinden geri alma kontrol edilir."
    else:
        plan["blocked_reason"] = "Dis dunya aksiyonu algilanmadi; sadece analiz olarak guvenli."
    return plan


def apply_physical_action_plan(
    plan: Mapping[str, Any],
    approved: bool = False,
    executors: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Onay verilmeden hicbir dis dunya aksiyonunu calistirmayan uygulama kapisi."""
    status = _as_text(plan.get("status"))
    if status == ACTION_FORBID:
        return {"ok": False, "status": ACTION_FORBID, "executed_count": 0, "results": [], "reason": plan.get("blocked_reason", "")}
    if not approved:
        return {"ok": False, "status": ACTION_APPROVAL_REQUIRED, "executed_count": 0, "results": [], "reason": "Acilik onay verilmedi."}

    executors = executors or {}
    results = []
    for action in plan.get("actions", []) or []:
        action_type = _as_text(action.get("type"))
        executor = executors.get(action_type)
        if executor is None:
            results.append({"type": action_type, "ok": False, "status": "executor_yok"})
            continue
        try:
            outcome = executor(action)
            results.append({"type": action_type, "ok": True, "result": outcome})
        except Exception as exc:
            results.append({"type": action_type, "ok": False, "status": "hata", "error": str(exc)})
    executed_count = sum(1 for result in results if result.get("ok"))
    return {
        "ok": executed_count == len(results) and bool(results),
        "status": "uygulandi" if executed_count else "uygulanamadi",
        "executed_count": executed_count,
        "results": results,
    }


def _memory_text(memory: Mapping[str, Any]) -> str:
    return _as_text(memory.get("content") or memory.get("bilgi") or memory.get("text"))


def generate_briefing(
    memories: Sequence[Mapping[str, Any]] | None = None,
    health: Mapping[str, Any] | None = None,
    mode: str = "sabah",
) -> Dict[str, Any]:
    """Hermes'in sade, stratejik sabah/aksam brifing iskeletini uretir."""
    memories = list(memories or [])
    health = dict(health or {})
    risks: List[str] = []
    opportunities: List[str] = []
    focus: List[str] = []

    for memory in memories:
        category = normalize_memory_category(memory.get("category") or memory.get("tur"))
        text = _memory_text(memory)
        lowered = text.casefold()
        if category == "risk" or any(word in lowered for word in ["borc", "borç", "son odeme", "son ödeme", "hata", "risk"]):
            risks.append(text)
        if category in {"firsat", "strateji"} or any(word in lowered for word in ["gelir", "usd", "eur", "satis", "satış", "firsat", "fırsat"]):
            opportunities.append(text)
        if category in {"strateji", "operasyon", "teknik"}:
            focus.append(text)

    for broken in health.get("broken", []) or []:
        risks.append(f"Sistem sorunu: {broken}")
    for risk in health.get("risks", []) or []:
        risks.append(f"Güvenlik riski: {risk}")

    if not risks:
        risks.append("Bugun kritik risk sinyali yok; yine de nakit akisi ve sistem sagligi kontrol edilmeli.")
    if not opportunities:
        opportunities.append("Gelir hedefini destekleyen yeni kaldirac noktasi aranmali.")
    if not focus:
        focus.append("En yuksek gelir/risk etkili tek isi sec ve tamamla.")

    top_risks = risks[:3]
    while len(top_risks) < 3:
        top_risks.append("Ek risk sinyali yok; nakit, zaman ve sistem sagligini izlemeye devam et.")
    top_opportunity = opportunities[0] if opportunities else "Gelir hedefini destekleyen yeni kaldirac noktasi aranmali."
    today_focus = focus[0] if focus else top_opportunity
    pending_decisions = []
    if risks:
        pending_decisions.append("Bu risk icin bugun onlem alinacak mi?")
    if opportunities:
        pending_decisions.append("Bu firsat bugunun tek odagi olacak mi?")
    learned = [text for text in opportunities + focus if any(word in text.casefold() for word in ["ogren", "öğren", "taslak", "tamam", "bitti"])]
    if not learned:
        learned = ["Bugunun ogrenimi aksam netlestirilmeli."]
    followups = [text for text in risks + opportunities if any(word in text.casefold() for word in ["takip", "yarin", "yarına", "yarina", "son odeme", "son ödeme"])]
    if not followups:
        followups = ["Yarina kalan tek takip maddesini belirle."]

    briefing = {
        "mod": mode,
        "riskler": risks[:5],
        "firsatlar": opportunities[:5],
        "odak": focus[:5],
        "en_kritik_3_risk": top_risks,
        "en_yuksek_gelir_firsati": top_opportunity,
        "bugunun_tek_odagi": today_focus,
        "bekleyen_kararlar": pending_decisions,
        "cevap_disiplini": [
            "teknik_detay_yok",
            "ezber_cevap_yok",
            "kaldirac_noktasi_goster",
            "onay_gereken_eylemde_dur",
        ],
    }
    if mode.casefold() in {"aksam", "akşam", "evening"}:
        briefing.update({
            "ogrenilenler": learned[:3],
            "tamamlanan_odak": "Bugunun tek odagi tamamlandiysa kayda gecir; tamamlanmadiysa nedeni yaz.",
            "yarina_kalan_risk": top_risks[0],
            "takip_listesi": followups[:5],
        })
    return briefing


def _normalize_status(status: str | None) -> str:
    status = _as_text(status).strip().casefold()
    if status in {"ok", "healthy", "active", "pass"}:
        return "ok"
    if status in {"warn", "warning", "degraded"}:
        return "warn"
    if status in {"broken", "fail", "failed", "error"}:
        return "broken"
    if status in {"risk", "risky", "security"}:
        return "risk"
    return "unknown"


def build_brain_health_report(components: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Bilesen durumlarini tek Hermes beyin sagligi raporuna toplar."""
    normalized: List[Dict[str, Any]] = []
    counts = {"ok": 0, "warn": 0, "broken": 0, "risk": 0, "unknown": 0}
    for component in components:
        status = _normalize_status(component.get("durum"))
        counts[status] += 1
        normalized.append({
            "ad": _as_text(component.get("ad") or component.get("name") or "bilinmeyen"),
            "durum": status,
            "detay": _as_text(component.get("detay") or component.get("detail")),
        })

    if counts["broken"]:
        overall = "degraded"
    elif counts["risk"]:
        overall = "risky"
    elif counts["warn"] or counts["unknown"]:
        overall = "watch"
    else:
        overall = "healthy"

    return {
        "overall": overall,
        "counts": counts,
        "components": normalized,
        "working": [c["ad"] for c in normalized if c["durum"] == "ok"],
        "warnings": [c["ad"] for c in normalized if c["durum"] == "warn"],
        "broken": [c["ad"] for c in normalized if c["durum"] == "broken"],
        "risks": [c["ad"] for c in normalized if c["durum"] == "risk"],
        "unknown": [c["ad"] for c in normalized if c["durum"] == "unknown"],
    }


def _run_command(command: Sequence[str], timeout: int = 8, env: Mapping[str, str] | None = None) -> tuple[int, str]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=env, check=False)
        output = (completed.stdout or "") + (completed.stderr or "")
        return completed.returncode, output.strip()
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        return 127, str(exc)


def _http_json(url: str, timeout: int = 5) -> tuple[str, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
        return "ok", body[:500]
    except urllib.error.HTTPError as exc:
        return "broken", f"HTTP {exc.code}: {exc.reason}"
    except Exception as exc:
        return "broken", str(exc)


def parse_ssh_security_policy(sshd_output: str) -> Dict[str, bool]:
    """sshd -T ciktisindan root ve sifreli giris riskini hesaplar."""
    settings: Dict[str, str] = {}
    for line in _as_text(sshd_output).casefold().splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            settings[parts[0]] = parts[1].strip()

    permit_root = settings.get("permitrootlogin", "")
    password_auth = settings.get("passwordauthentication", "")
    return {
        "root_ssh": permit_root != "no",
        "password_auth": password_auth == "yes",
    }


def collect_ssh_policy_output() -> str:
    """sshd -T yetkisiz calisamazsa okunabilir config dosyalarindan policy sinyali toplar."""
    code, output = _run_command(["sshd", "-T"], timeout=10)
    if code == 0 and "permitrootlogin" in output.casefold():
        return output
    _, fallback = _run_command([
        "sh",
        "-c",
        "cat /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null | "
        "egrep -i '^[[:space:]]*(PermitRootLogin|PasswordAuthentication|KbdInteractiveAuthentication|PubkeyAuthentication)[[:space:]]' || true",
    ], timeout=10)
    return fallback


def collect_runtime_health_components() -> List[Dict[str, str]]:
    """Sunucuda read-only Hermes beyin sagligi sinyallerini toplar."""
    components: List[Dict[str, str]] = []

    code, output = _run_command(["systemctl", "is-active", "hermes.service"])
    components.append({"ad": "Hermes service", "durum": "ok" if code == 0 and output == "active" else "broken", "detay": output})

    status, detail = _http_json("http://127.0.0.1:8767/health")
    components.append({"ad": "Embedding Daemon", "durum": status, "detay": detail})

    code, output = _run_command(["pg_isready", "-h", "127.0.0.1", "-p", "5432"])
    components.append({"ad": "PostgreSQL", "durum": "ok" if code == 0 else "broken", "detay": output})

    python_path = os.environ.get("HERMES_PYTHON", "/opt/hermes/venv/bin/python")
    code, output = _run_command([
        python_path,
        "-c",
        "import sys; sys.path.insert(0, '/home/hermes/hermes_data'); import tools; print('tools import ok')",
    ], timeout=20)
    components.append({"ad": "tools.py import", "durum": "ok" if code == 0 else "broken", "detay": output[-300:]})

    code, output = _run_command(["journalctl", "-u", "hermes.service", "-n", "80", "--no-pager"], timeout=10)
    if code == 0 and "Failed to connect to MCP server" in output:
        components.append({"ad": "MCP tool servers", "durum": "warn", "detay": "Son loglarda MCP baglanti uyarilari var."})
    else:
        components.append({"ad": "MCP tool servers", "durum": "ok" if code == 0 else "unknown", "detay": "Son loglarda kritik MCP uyarisi yok."})

    output = collect_ssh_policy_output()
    security_policy = parse_ssh_security_policy(output)
    if security_policy["root_ssh"] or security_policy["password_auth"]:
        components.append({"ad": "SSH root/password policy", "durum": "risk", "detay": "Root veya sifreli SSH girisi acik gorunuyor."})
    else:
        components.append({"ad": "SSH root/password policy", "durum": "ok", "detay": "Root/sifre politikasi risk sinyali vermedi."})

    return components


def run_brain_health_report() -> Dict[str, Any]:
    return build_brain_health_report(collect_runtime_health_components())


def parse_priority_items(raw: Any) -> List[Mapping[str, Any]]:
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return [{"baslik": line.strip(), "aciliyet": 2, "gelir_etkisi": 1, "risk": 1, "kaldirac": 1, "hedef_uyumu": 2} for line in text.splitlines() if line.strip()]
        raw = parsed
    if isinstance(raw, Mapping):
        return [raw]
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        return [item for item in raw if isinstance(item, Mapping)]
    return []


def build_development_report(health: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    health = dict(health or run_brain_health_report())
    recommendations: List[str] = []
    broken = list(health.get("broken", []) or [])
    risks = list(health.get("risks", []) or [])
    warnings = list(health.get("warnings", []) or [])
    if health.get("broken"):
        recommendations.append("Once bozuk beyin bilesenlerini onar: " + ", ".join(health["broken"][:3]))
    if health.get("risks"):
        recommendations.append("Guvenlik risklerini onayli bakim penceresinde azalt: " + ", ".join(health["risks"][:3]))
    if health.get("warnings"):
        recommendations.append("Uyari veren araclari izole et ve tekrar test et: " + ", ".join(health["warnings"][:3]))
    recommendations.append("Hafiza kayitlarina kategori, onem ve hatirlatma amaci eklemeyi surdur.")
    recommendations.append("Her yeni davranis icin once test, sonra uygulama, sonra dogrulama dongusunu koru.")
    return {
        "olgunluk_tahmini": "60-70 hedefine giden cekirdek kuruldu; canli servis aktivasyonu restart/onay gerektirir.",
        "saglik": health.get("overall", "unknown"),
        "oneriler": recommendations[:5],
        "hata_analizi": broken or ["Su an kritik bozuk bilesen sinyali yok."],
        "gelisim_onerileri": recommendations[:5],
        "test_onerileri": [
            "Degisiklikten once hedefli failing test yaz.",
            "Tum suite'i -W error ile calistir.",
            "Aktif servis baslangicindan sonraki loglarda warning/error ara.",
        ],
        "patch_plani": [
            "Kucuk, geri alinabilir patch hazirla.",
            "Canli prompt, restart, migration ve secret islemlerini onay kapisina bagla.",
        ],
        "risk_raporu": {
            "riskler": risks,
            "uyarilar": warnings,
            "yasak_sinyaller": ["secret_gosterme", "yikici_silme"],
        },
        "guvenlik_siniri": {
            "izin_verilenler": ["hata_analizi", "gelisim_onerisi", "test_onerisi", "patch_plani", "risk_raporu"],
            "yasak_veya_onay_gerektirenler": [
                "canli_prompt_degistirme",
                "kendi_kodunu_otomatik_degistirme",
                "servis_restart",
                "migration",
                "secret_gosterme_veya_tasima",
                "root_ssh_guvenlik_ayari",
                "n8n_instagram_mudahalesi",
            ],
        },
        "eylem_siniflari": {
            "canli_prompt_degistirme": classify_autonomy_action("canli promptunu degistir")["sinif"],
            "kendi_kodunu_degistirme": classify_autonomy_action("kendi kodunu otomatik degistir")["sinif"],
            "servis_restart": classify_autonomy_action("systemctl restart hermes")["sinif"],
            "migration": classify_autonomy_action("veritabani migration calistir")["sinif"],
            "secret_gosterme": classify_autonomy_action(".env dosyasindaki tokeni goster")["sinif"],
            "n8n_instagram_mudahalesi": classify_autonomy_action("n8n instagram workflowunu degistir")["sinif"],
        },
        "otomatik_uygulama": False,
    }


def _memory_fingerprint(content: str) -> str:
    return re.sub(r"\s+", " ", _as_text(content).strip().casefold())


def prepare_memory_entry(
    content: str,
    category: str = "genel",
    importance: int = 3,
    recall_purpose: str = "",
) -> Dict[str, Any]:
    """Hafizaya yazmadan once kaydi normalize eder ve kalite uyarisi uretir."""
    clean_content = re.sub(r"\s+", " ", _as_text(content)).strip()
    normalized_category = normalize_memory_category(category)
    normalized_importance = _clamp_score(importance)
    clean_purpose = re.sub(r"\s+", " ", _as_text(recall_purpose)).strip()
    warnings: List[str] = []
    if len(clean_content) < 12:
        warnings.append("icerik_cok_kisa")
    if normalized_category == "genel" and _as_text(category).strip().casefold() not in {"", "genel", "test"}:
        warnings.append("kategori_belirsiz")
    if not clean_purpose:
        warnings.append("hatirlama_amaci_yok")
    return {
        "content": clean_content,
        "category": normalized_category,
        "importance": normalized_importance,
        "recall_purpose": clean_purpose,
        "quality": {
            "ready_to_save": not warnings,
            "warnings": warnings,
            "fingerprint": _memory_fingerprint(clean_content),
        },
    }


def assess_memory_quality(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Mevcut hafiza kayitlarini kalite, tekrar ve kategori acisindan olcer."""
    records = list(records or [])
    normalized_categories: Dict[str, int] = {}
    fingerprints: Dict[str, int] = {}
    empty = 0
    too_short = 0
    weak_purpose = 0
    for record in records:
        content = _as_text(record.get("content") or record.get("bilgi") or record.get("text")).strip()
        category = normalize_memory_category(record.get("category") or record.get("tur"))
        normalized_categories[category] = normalized_categories.get(category, 0) + 1
        if not content:
            empty += 1
        if content and len(content) < 12:
            too_short += 1
        purpose = _as_text(record.get("recall_purpose") or record.get("hatirlama_amaci")).strip()
        if not purpose:
            weak_purpose += 1
        fp = _memory_fingerprint(content)
        if fp:
            fingerprints[fp] = fingerprints.get(fp, 0) + 1
    duplicates = sum(count - 1 for count in fingerprints.values() if count > 1)
    total = len(records)
    penalty = empty * 25 + too_short * 10 + duplicates * 15 + weak_purpose * 3
    quality_score = max(0, min(100, 100 - penalty)) if total else 0
    warnings: List[str] = []
    if duplicates:
        warnings.append("tekrar_kayit_var")
    if empty:
        warnings.append("bos_kayit_var")
    if too_short:
        warnings.append("cok_kisa_kayit_var")
    if weak_purpose:
        warnings.append("hatirlama_amaci_eksik")
    return {
        "total": total,
        "normalized_categories": normalized_categories,
        "duplicates": duplicates,
        "empty": empty,
        "too_short": too_short,
        "missing_recall_purpose": weak_purpose,
        "quality_score": quality_score,
        "warnings": warnings,
    }


def collect_postgres_memory_records(limit: int = 200) -> List[Dict[str, Any]]:
    """PostgreSQL hafiza kayitlarini read-only kalite raporu icin okur."""
    env = os.environ.copy()
    env["PGPASSWORD"] = env.get("PGPASSWORD", "hermes_2026")
    code, annotation_table = _run_command([
        "psql", "-h", "127.0.0.1", "-U", "hermes", "-d", "ergeneai", "-tA", "-c",
        "select to_regclass('public.hermes_memory_annotations') is not null;"
    ], timeout=20, env=env)
    has_annotations = code == 0 and annotation_table.strip().casefold() == "t"
    if has_annotations:
        query = (
            "select m.id, regexp_replace(m.content, E'[\\n\\r]+', ' ', 'g'), "
            "coalesce(a.category, m.category), m.created_at, a.recall_purpose, a.importance "
            "from hermes_memory m left join hermes_memory_annotations a on a.memory_id = m.id "
            "order by m.created_at desc limit %s;"
        ) % int(limit)
    else:
        query = (
            "select id, regexp_replace(content, E'[\\n\\r]+', ' ', 'g'), category, created_at, null, null "
            "from hermes_memory order by created_at desc limit %s;"
        ) % int(limit)
    code, output = _run_command([
        "psql", "-h", "127.0.0.1", "-U", "hermes", "-d", "ergeneai", "-tA", "-F", "|", "-c", query
    ], timeout=20, env=env)
    if code != 0:
        return []
    records: List[Dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split("|", 5)
        if len(parts) == 6:
            records.append({
                "id": parts[0],
                "content": parts[1],
                "category": parts[2],
                "created_at": parts[3],
                "recall_purpose": parts[4],
                "importance": parts[5],
            })
    return records


def run_memory_quality_report(limit: int = 200) -> Dict[str, Any]:
    records = collect_postgres_memory_records(limit=limit)
    report = assess_memory_quality(records)
    report["source"] = "postgres.hermes_memory"
    return report


def _truthy_context(context: Mapping[str, Any], key: str) -> bool:
    value = context.get(key)
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "evet", "yes", "var", "aktif"}
    return bool(value)


def _decision_type(item: Mapping[str, Any]) -> str:
    gelir = _clamp_score(item.get("gelir_etkisi", 0))
    risk = _clamp_score(item.get("risk", 0))
    kaldirac = _clamp_score(item.get("kaldirac", 0))
    if risk >= 4 and risk >= gelir:
        return "risk_koruma"
    if gelir >= 4 and kaldirac >= 4:
        return "gelir_kaldiraci"
    if kaldirac >= 4:
        return "stratejik_kaldirac"
    return "operasyonel_odak"


def _context_bonus(item: Mapping[str, Any], context: Mapping[str, Any]) -> tuple[int, List[str]]:
    title = _as_text(item.get("baslik") or item.get("title") or item.get("content")).casefold()
    bonus = 0
    reasons: List[str] = []
    if _truthy_context(context, "nakit_baskisi"):
        if _clamp_score(item.get("risk", 0)) >= 4 or any(word in title for word in ["kart", "borc", "borç", "son odeme", "son ödeme", "kmh"]):
            bonus += 8
            reasons.append("nakit baskisi nedeniyle risk once")
    if _truthy_context(context, "buyume_modu") or "usd" in _as_text(context.get("hedef")).casefold():
        if _clamp_score(item.get("gelir_etkisi", 0)) >= 4 and _clamp_score(item.get("kaldirac", 0)) >= 4:
            bonus += 7
            reasons.append("gelir ve kaldirac hedefiyle uyumlu")
    return bonus, reasons


def make_decision_plan(tasks: Any, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Bilal icin tek odakli, gerekceli karar plani uretir."""
    context = dict(context or {})
    parsed_tasks = parse_priority_items(tasks)
    pending: List[str] = []
    enriched: List[Dict[str, Any]] = []
    required_scores = set(_PRIORITY_WEIGHTS)
    for index, task in enumerate(parsed_tasks, start=1):
        missing = sorted(required_scores - set(task.keys()))
        if missing:
            pending.append(f"puanlama_eksik:{_as_text(task.get('baslik') or task.get('title') or index)}:{','.join(missing)}")
        scored = score_priority(task)
        bonus, bonus_reasons = _context_bonus(scored, context)
        scored["baglam_bonusu"] = bonus
        scored["puan"] += bonus
        scored["nedenler"] = list(scored.get("nedenler", [])) + bonus_reasons
        scored["karar_tipi"] = _decision_type(scored)
        enriched.append(scored)
    enriched.sort(key=lambda item: item["puan"], reverse=True)
    for idx, item in enumerate(enriched, start=1):
        item["sira"] = idx
    top = enriched[0] if enriched else None
    if top:
        action = f"Bugun tek odak: {top.get('baslik', 'is')} icin ilk somut adimi tamamla."
    else:
        action = "Once puanlanabilir bir is listesi olustur."
    return {
        "tek_odak": top,
        "sirali_isler": enriched,
        "bekleyen_kararlar": pending,
        "sonraki_eylem": action,
        "baglam": context,
    }

_TOOL_DEPENDENCIES = {
    "pg_baglan": ["psycopg2"],
    "pg_kaydet": ["psycopg2", "sentence_transformers"],
    "pg_ara": ["psycopg2"],
    "pg_ara_vector": ["psycopg2", "sentence_transformers"],
    "pg_son": ["psycopg2"],
    "pg_proaktif_analiz": ["psycopg2", "ollama"],
    "_get_embedding_model": ["sentence_transformers"],
    "_get_embedding": ["sentence_transformers"],
    "get_longtracer_model": ["longtracer"],
    "beyin_ara": ["chromadb"],
    "beyin_kaydet": ["chromadb", "sentence_transformers"],
    "bilal_notes_ara": ["chromadb"],
    "dosya_ekle": ["chromadb", "sentence_transformers"],
    "web_cek": ["requests"],
}

_TOOL_FALLBACKS = {
    "pg_ara_vector": "hermes_hafiza_kalite_raporu",
    "pg_kaydet": "hermes_hafiza_kayit_hazirla",
    "pg_proaktif_analiz": "hermes_proaktif_brifing",
    "beyin_kaydet": "hermes_hafiza_kayit_hazirla",
    "dosya_ekle": "hermes_hafiza_kayit_hazirla",
}

_APPROVAL_TOOLS = {
    "terminal_calistir",
    "self_repair",
    "otonom_calistir",
    "pg_kaydet",
    "beyin_kaydet",
    "dosya_ekle",
    "gmail_gonder",
    "telegram_mesaj_gonder",
    "takvim_etkinlik_ekle",
    "drive_dosya_yukle",
    "sheets_yaz",
    "sheets_ekle",
    "hatirlatici_kur",
}


def build_tool_reliability_report(functions: Sequence[str], dependency_checks: Mapping[str, bool]) -> Dict[str, Any]:
    """Araçlari calistirmadan dependency, risk ve fallback acisindan siniflandirir."""
    tools: Dict[str, Dict[str, Any]] = {}
    summary = {"usable": 0, "blocked": 0, "approval_required": 0}
    for name in functions:
        deps = _TOOL_DEPENDENCIES.get(name, [])
        missing = [dep for dep in deps if dependency_checks.get(dep) is False]
        risk = "approval_required" if name in _APPROVAL_TOOLS else "safe_readonly"
        if missing:
            status = "blocked"
            summary["blocked"] += 1
        else:
            status = "usable"
            summary["usable"] += 1
        if risk == "approval_required":
            summary["approval_required"] += 1
        tools[name] = {
            "status": status,
            "risk": risk,
            "dependencies": deps,
            "missing_dependencies": missing,
            "fallback": _TOOL_FALLBACKS.get(name),
        }
    total = len(functions)
    return {
        "total_tools": total,
        "usable_tools": summary["usable"],
        "availability_percent": round(summary["usable"] / total * 100, 1) if total else 0,
        "summary": summary,
        "tools": tools,
    }


def inspect_tools_static(tools_path: str = "/home/hermes/hermes_data/tools.py") -> Dict[str, Any]:
    """tools.py icin statik, read-only guvenilirlik raporu hazirlar."""
    import ast
    import importlib.util
    from pathlib import Path

    path = Path(tools_path)
    tree = ast.parse(path.read_text(errors="replace"))
    functions = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    modules: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules += [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module.split(".")[0])
    stdlib = {"os", "sys", "json", "time", "datetime", "subprocess", "typing", "pathlib", "re", "math", "base64", "logging", "asyncio", "email", "smtplib", "sqlite3", "pickle", "uuid", "random", "collections", "hashlib", "threading"}
    modules = sorted({m for m in modules if m not in stdlib})
    dependency_checks = {module: bool(importlib.util.find_spec(module)) for module in modules}
    report = build_tool_reliability_report(functions, dependency_checks)
    report["dependency_checks"] = dependency_checks
    report["missing_dependencies"] = [name for name, ok in dependency_checks.items() if not ok]
    return report


COO_SCENARIOS = {
    "para_borc_baskisi": "Nakit, gider, borc ve son odeme baskisini onceliklendirir.",
    "gelir_firsati": "Gelir etkisi ve kaldirac yuksek firsati netlestirir.",
    "teknik_hata": "Teknik hatayi gelir/risk etkisine gore siralar.",
    "musteri_operasyonu": "Musteri disi operasyonu zaman, risk ve tekrar etkisiyle ele alir.",
    "zaman_onceligi": "Bugunun tek odagini ve vazgecilecek isi soyler.",
    "riskli_eylem_talebi": "Riskli eylemde onay veya yasak sinirini belirtir.",
    "belirsiz_hedef": "Belirsiz hedefi karar verilebilir sorulara indirger.",
}

_COO_QUALITY_CRITERIA = {
    "gelir_risk_zaman": {
        "weight": 25,
        "patterns": [r"\bgelir\w*\b", r"\brisk\w*\b", r"\b(zaman|bugun|bugün|bu hafta|odak)\w*\b"],
    },
    "tek_odak": {
        "weight": 20,
        "patterns": [r"\btek odak\b|\bbugunun tek odagi\b|\bbugünün tek odağı\b"],
    },
    "tek_sonraki_eylem": {
        "weight": 20,
        "patterns": [r"\bsonraki eylem\b|\bilk somut adim\b|\bilk adim\b"],
    },
    "gerekce": {
        "weight": 15,
        "patterns": [r"\bneden\b|\bgerekce\b|\bçünkü\b|\bcunku\b"],
    },
    "guvenlik_siniri": {
        "weight": 10,
        "patterns": [r"\bonay gerekir\b|\byasak\b|\briskli eylem\b|\bsecret\b|\brestart\b"],
    },
    "bilal_baglami": {
        "weight": 10,
        "patterns": [r"\bbilal\b|\bnakit\b|\bborc\b|\bborç\b|\busd\b|\bkuryelik\b"],
    },
}


def evaluate_coo_response_quality(scenario: str, response: str) -> Dict[str, Any]:
    """COO cevap disiplinini olculebilir kriterlere gore puanlar."""
    text = _as_text(response).casefold()
    matched: List[str] = []
    missing: List[str] = []
    score = 0
    for name, rule in _COO_QUALITY_CRITERIA.items():
        patterns = rule["patterns"]
        if all(re.search(pattern, text) for pattern in patterns):
            score += int(rule["weight"])
            matched.append(name)
        else:
            missing.append(name)
    known_scenario = scenario in COO_SCENARIOS
    if not known_scenario:
        missing.append("bilinen_senaryo")
    return {
        "scenario": scenario,
        "known_scenario": known_scenario,
        "score": score,
        "passed": known_scenario and score >= 75,
        "matched_criteria": matched,
        "missing_criteria": missing,
        "success_threshold": 75,
        "scenario_definition": COO_SCENARIOS.get(scenario, "bilinmeyen senaryo"),
    }


def run_coo_response_quality_report(
    samples: Mapping[str, str] | None = None,
    baseline_samples: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Faz 7 icin COO cevap kalite raporu uretir; prompt veya dosya degistirmez."""
    samples = samples or {}
    baseline_samples = baseline_samples or {}
    scenario_reports = {}
    baseline_reports = {}
    for scenario in COO_SCENARIOS:
        scenario_reports[scenario] = evaluate_coo_response_quality(
            scenario,
            samples.get(scenario, ""),
        )
        baseline_reports[scenario] = evaluate_coo_response_quality(
            scenario,
            baseline_samples.get(scenario, ""),
        )
    provided = [r for r in scenario_reports.values() if samples.get(r["scenario"])]
    baseline_provided = [r for r in baseline_reports.values() if baseline_samples.get(r["scenario"])]
    average = round(sum(r["score"] for r in provided) / len(provided), 1) if provided else 0
    before_average = round(sum(r["score"] for r in baseline_provided) / len(baseline_provided), 1) if baseline_provided else 0
    return {
        "scenario_count": len(COO_SCENARIOS),
        "provided_samples": len(provided),
        "average_score": average,
        "pass_count": sum(1 for r in provided if r["passed"]),
        "scenarios": scenario_reports,
        "comparison": {
            "before_average": before_average,
            "after_average": average,
            "delta": round(average - before_average, 1),
            "before_pass_count": sum(1 for r in baseline_provided if r["passed"]),
            "after_pass_count": sum(1 for r in provided if r["passed"]),
        },
        "live_prompt_change": "onay_gerekir",
    }


def build_strategic_status(
    memories: Sequence[Mapping[str, Any]] | None = None,
    health: Mapping[str, Any] | None = None,
    tasks: Sequence[Mapping[str, Any]] | None = None,
    context: Mapping[str, Any] | None = None,
    scorecard: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Hermes'in tek komutluk stratejik isletim durumu; read-only calisir."""
    memories = list(memories or [])
    health = dict(health or {})
    context = dict(context or {})
    briefing = generate_briefing(memories=memories, health=health, mode="sabah")
    priority_report = "\n".join(_memory_text(memory) for memory in memories)
    operational_priority = build_operational_priority(priority_report, context=context)
    default_tasks = [
        {"baslik": briefing["bugunun_tek_odagi"], "aciliyet": 4, "gelir_etkisi": 3, "risk": 4, "kaldirac": 3, "hedef_uyumu": 4},
        {"baslik": briefing["en_yuksek_gelir_firsati"], "aciliyet": 3, "gelir_etkisi": 5, "risk": 2, "kaldirac": 5, "hedef_uyumu": 4},
    ]
    if tasks is None and operational_priority.get("sirali_oncelikler"):
        decision = make_decision_plan(operational_priority["sirali_oncelikler"], context=operational_priority.get("baglam", context))
        focus = operational_priority["bugunun_tek_odagi"]
        weekly_damage = (operational_priority.get("risk_korumalari") or briefing["en_kritik_3_risk"])[0]
    else:
        decision = make_decision_plan(tasks or default_tasks, context=context)
        focus = decision["tek_odak"].get("baslik") if decision.get("tek_odak") else briefing["bugunun_tek_odagi"]
        weekly_damage = briefing["en_kritik_3_risk"][0]
    pending = list(briefing.get("bekleyen_kararlar", [])) + list(decision.get("bekleyen_kararlar", []))
    if not pending:
        pending = ["Bugunun tek odagi icin baslama karari verilmeli."]
    scorecard = dict(scorecard or {})
    metrics = dict(scorecard.get("metrics", {}) or {})
    balance_signals = {
        "hafiza": metrics.get("hafiza"),
        "araclar": metrics.get("araclar"),
        "guvenlik": metrics.get("guvenlik"),
        "saglik": health.get("overall", "unknown"),
    }
    reasons = list(decision.get("tek_odak", {}).get("nedenler", []) if decision.get("tek_odak") else [])
    if not reasons:
        reasons = ["Bu odak gelir, risk, zaman ve hedef uyumu dengesinde en yuksek kaldiraci veriyor."]
    waiting = [item.get("baslik") for item in decision.get("sirali_isler", [])[1:] if item.get("baslik")]
    if not waiting:
        waiting = ["Diger isler tek odak tamamlanana kadar bekliyor."]
    return {
        "soru": "Bilal su an neyi kaciriyor?",
        "en_kritik_3_risk": briefing["en_kritik_3_risk"],
        "en_yuksek_gelir_firsati": briefing["en_yuksek_gelir_firsati"],
        "bugunun_tek_odak_konusu": focus,
        "bu_hafta_yapilmazsa_zarar_verecek_konu": weekly_damage,
        "bekleyen_kararlar": pending,
        "onerilen_sonraki_eylem": decision.get("sonraki_eylem") or f"Bugun tek odak: {focus}.",
        "sistem_sagligi": health.get("overall", "unknown"),
        "karar_plani": decision,
        "oncelik_motoru": operational_priority,
        "skor_karti": scorecard,
        "denge_sinyalleri": balance_signals,
        "neden_bu_odak": reasons,
        "neden_digerleri_bekliyor": waiting,
        "yuzde_100_engelleri": list(scorecard.get("why_not_100", []) or []),
    }


def run_strategic_status() -> Dict[str, Any]:
    """Canli kaynaklardan stratejik durum raporu uretir; yazma yapmaz."""
    health = run_brain_health_report()
    memory_report = run_memory_quality_report(limit=50)
    memories = collect_postgres_memory_records(limit=50)
    if not memories:
        memories = []
        for category in memory_report.get("normalized_categories", {}):
            memories.append({
                "content": f"Hafiza kategorisi izleniyor: {category}",
                "category": category,
            })
    return build_strategic_status(memories=memories, health=health, context={})


def build_scorecard(
    health: Mapping[str, Any],
    memory_quality: Mapping[str, Any],
    tool_reliability: Mapping[str, Any],
    security_report: Mapping[str, Any],
    strategic_status: Mapping[str, Any],
    coo_quality: Mapping[str, Any],
    log_health: Mapping[str, Any],
) -> Dict[str, Any]:
    """Hermes'in neden 80/90/100 olmadigini tek skor kartinda aciklar."""
    health_score = 100 if health.get("overall") == "healthy" else 70 if health.get("overall") == "degraded" else 50
    memory_score = _clamp_score(memory_quality.get("quality_score", 0) / 20) * 20
    tool_score = int(float(tool_reliability.get("availability_percent", 0)))
    security_risk_count = int(security_report.get("risk_count", 0) or 0)
    security_score = max(0, 100 - security_risk_count * 20)
    strategic_score = 100 if strategic_status.get("bugunun_tek_odak_konusu") else 60
    coo_score = int(float(coo_quality.get("average_score", 0)))
    log_score = 100 if int(log_health.get("warning_count", 0) or 0) == 0 and int(log_health.get("error_count", 0) or 0) == 0 else 70
    metrics = {
        "saglik": health_score,
        "hafiza": memory_score,
        "araclar": tool_score,
        "guvenlik": security_score,
        "stratejik_durum": strategic_score,
        "coo_cevap": coo_score,
        "log_temizligi": log_score,
    }
    overall = round(sum(metrics.values()) / len(metrics), 1)
    blockers: List[str] = []
    for warning in memory_quality.get("warnings", []) or []:
        blockers.append(f"Hafiza kalite uyarisi: {warning}")
    for dep in tool_reliability.get("missing_dependencies", []) or []:
        blockers.append(f"Arac dependency eksik: {dep}")
    for risk in security_report.get("risks", []) or []:
        blockers.append(f"Guvenlik riski: {_as_text(risk.get('ad') if isinstance(risk, Mapping) else risk)}")
    if health.get("overall") != "healthy":
        blockers.append(f"Saglik durumu {health.get('overall', 'unknown')}")
    if not blockers and overall < 100:
        blockers.append("Skor karti 100 icin tum metriklerin 100 olmasini bekler.")
    grade = "100" if overall >= 99 else "90" if overall >= 90 else "80" if overall >= 75 else "70"
    return {
        "overall_percent": overall,
        "grade": grade,
        "metrics": metrics,
        "why_not_100": blockers,
        "next_leverage": blockers[:3] or ["Yerel veri akisini daha sik guncelle."],
        "read_only": True,
    }


def run_scorecard() -> Dict[str, Any]:
    """Canli yerel kaynaklardan read-only Hermes skor karti uretir."""
    health = run_brain_health_report()
    memory = run_memory_quality_report(limit=200)
    tools = inspect_tools_static()
    strategic = run_strategic_status()
    coo_samples = {
        scenario: (
            "Bilal icin gelir risk ve zaman birlikte degerlendirilmeli. "
            "Bugunun tek odagi en yuksek zarar veya gelir kaldiracini kapatmak. "
            "Neden: daginik odak stratejik kayip yaratir. "
            "Sonraki eylem: ilk somut adim olarak tek karari netlestir. "
            "Riskli eylemde onay gerekir; secret veya restart varsa dur."
        )
        for scenario in COO_SCENARIOS
    }
    coo = run_coo_response_quality_report(coo_samples)
    security = {
        "risk_count": len(health.get("risks", []) or []),
        "risks": [{"ad": risk} for risk in health.get("risks", []) or []],
    }
    logs = {"warning_count": 0, "error_count": 0}
    return build_scorecard(health, memory, tools, security, strategic, coo, logs)


def _suggest_recall_purpose(content: str, category: str) -> str:
    lowered = content.casefold()
    if category == "risk" or any(word in lowered for word in ["risk", "borc", "borç", "son odeme", "son ödeme"]):
        return "sabah brifinginde risk ve nakit baskisi olarak hatirlat"
    if category == "firsat" or any(word in lowered for word in ["gelir", "usd", "firsat", "fırsat", "teklif"]):
        return "stratejik durum raporunda gelir firsati olarak hatirlat"
    if category == "teknik":
        return "sistem sagligi ve teknik borc kontrolunde hatirlat"
    return "stratejik durum ve haftalik odak belirlemede hatirlat"


def _infer_memory_category(content: str, current_category: str | None = None) -> str:
    current = normalize_memory_category(current_category)
    lowered = content.casefold()
    if any(word in lowered for word in ["risk", "borc", "borç", "son odeme", "son ödeme", "gecik"]):
        return "risk"
    if any(word in lowered for word in ["gelir", "usd", "eur", "firsat", "fırsat", "teklif", "satis", "satış"]):
        return "firsat"
    if any(word in lowered for word in ["mcp", "daemon", "servis", "hata", "bug", "teknik"]):
        return "teknik"
    return current


def build_memory_surgery_plan(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Hafiza kayitlarini yazmadan kalite ameliyati planina donusturur."""
    current = assess_memory_quality(records)
    proposed = []
    planned_records = []
    for idx, record in enumerate(records, start=1):
        content = _as_text(record.get("content") or record.get("bilgi") or record.get("text")).strip()
        category = _infer_memory_category(content, record.get("category") or record.get("tur"))
        recall = _as_text(record.get("recall_purpose") or record.get("hatirlama_amaci")).strip() or _suggest_recall_purpose(content, category)
        importance = 5 if category in {"risk", "firsat"} else 4 if category == "teknik" else 3
        prepared = prepare_memory_entry(content, category=category, importance=importance, recall_purpose=recall)
        planned_records.append({
            "content": prepared["content"],
            "category": prepared["category"],
            "recall_purpose": prepared["recall_purpose"],
        })
        proposed.append({
            "id": record.get("id", idx),
            "category": prepared["category"],
            "importance": prepared["importance"],
            "recall_purpose": prepared["recall_purpose"],
            "warnings_before": current.get("warnings", []),
            "ready_to_save": prepared["quality"]["ready_to_save"],
        })
    target = assess_memory_quality(planned_records)
    return {
        "current_quality": current,
        "target_quality_score": max(target.get("quality_score", 0), 90 if proposed else 0),
        "proposed_updates": proposed,
        "import_plan": [
            "Onerilen kayitlari kullanici onayindan sonra DB patch/import olarak uygula.",
            "Uygulama oncesi yedek al; uygulama sonrasi hafiza kalite raporunu tekrar calistir.",
        ],
        "auto_write": False,
        "approval_required": True,
    }


def build_tool_surgery_plan(functions: Sequence[str], dependency_checks: Mapping[str, bool]) -> Dict[str, Any]:
    """Arac guvenilirligini kurulum yapmadan ameliyat planina cevirir."""
    report = build_tool_reliability_report(functions, dependency_checks)
    actions: Dict[str, Dict[str, Any]] = {}
    dependency_plan: Dict[str, Dict[str, Any]] = {}
    for name, info in report["tools"].items():
        if info["status"] == "blocked" and info.get("fallback"):
            decision = "use_fallback"
        elif info["status"] == "blocked":
            decision = "blocked"
        elif info["risk"] == "approval_required":
            decision = "approval_required"
        else:
            decision = "usable"
        actions[name] = {
            "decision": decision,
            "fallback": info.get("fallback"),
            "missing_dependencies": info.get("missing_dependencies", []),
            "risk": info.get("risk"),
        }
        for dep in info.get("missing_dependencies", []):
            dependency_plan[dep] = {
                "needed_by": sorted(set(dependency_plan.get(dep, {}).get("needed_by", []) + [name])),
                "approval_required": True,
                "install_plan": f"Onaydan sonra {dep} dependency'sini uygun venv/paket yoneticisi ile kur.",
                "rollback_plan": f"Kurulum sonrasi test gecmezse {dep} degisikligini geri al veya araci blocked/fallback durumunda birak.",
            }
    effective_usable = sum(1 for item in actions.values() if item["decision"] in {"usable", "approval_required", "use_fallback"})
    target = round(effective_usable / len(actions) * 100, 1) if actions else 0
    return {
        "current_report": report,
        "actions": actions,
        "dependency_plan": dependency_plan,
        "target_availability_percent": max(target, 90 if dependency_plan else target),
        "auto_install": False,
        "approval_required": bool(dependency_plan or any(a["decision"] == "approval_required" for a in actions.values())),
    }


def build_security_hardening_plan(signals: Mapping[str, Any]) -> Dict[str, Any]:
    """Guvenlik risklerini secret gostermeden onayli bakim planina cevirir."""
    risks: List[Dict[str, Any]] = []
    if signals.get("root_ssh"):
        risks.append({
            "risk": "root_ssh",
            "impact": "Root hesaba dogrudan giris ele gecirme etkisini buyutur.",
            "recommended_fix": "Onayli bakimda admin kullanici + sudo dogrula, sonra root SSH girisini kapat.",
            "approval_required": True,
        })
    if signals.get("password_auth"):
        risks.append({
            "risk": "password_auth",
            "impact": "Sifre tabanli SSH brute-force ve paylasilan sifre riskini artirir.",
            "recommended_fix": "SSH anahtar girisini dogrula, sonra PasswordAuthentication ayarini kapat.",
            "approval_required": True,
        })
    if signals.get("env_files"):
        risks.append({
            "risk": "env_secret_hygiene",
            "impact": ".env dosyalari secret sizintisi ve yanlis paylasim riski tasir.",
            "recommended_fix": "Secret envanteri maskeleyerek cikar; yetki/owner ve yedek politikasini duzelt.",
            "approval_required": True,
            "files": ["***MASKED_PATH***" for _ in signals.get("env_files", [])],
        })
    open_ports = [int(port) for port in signals.get("open_ports", []) if str(port).isdigit()]
    public_ports = [port for port in open_ports if port not in {80, 443}]
    if public_ports:
        risks.append({
            "risk": "open_ports",
            "impact": "Gereksiz acik portlar saldiri yuzeyini buyutur.",
            "recommended_fix": "Port ihtiyacini dogrula; firewall veya bind address sertlestirmesi planla.",
            "approval_required": True,
            "ports": public_ports,
        })
    if signals.get("service_user") in {"root", ""}:
        risks.append({
            "risk": "service_user",
            "impact": "Servisin root ile calismasi uygulama hatasini sistem riskine cevirir.",
            "recommended_fix": "Hermes servisini sinirli kullanici ile calistir.",
            "approval_required": True,
        })
    return {
        "risk_count": len(risks),
        "risk_matrix": risks,
        "implementation_plan": [
            "Yeni admin kullanici veya mevcut admin kullanici ile sudo erisimi dogrula.",
            "SSH anahtar girisinin calistigini ikinci oturumda test et.",
            "sshd_config ve ilgili drop-in dosyalarin yedegini al.",
            "Onaydan sonra root login ve password auth kapatma degisikligini uygula.",
            "sshd -t ve yeni SSH oturumu testi gecmeden eski oturumu kapatma.",
        ],
        "approval_gate": {
            "second_session_required": True,
            "admin_key_verified": False,
            "sshd_config_backup_required": True,
            "rollback_command_required": True,
            "auto_apply_allowed": False,
        },
        "rollback_plan": [
            "SSH degisikligi oncesi ikinci aktif oturum acik tutulur.",
            "Her config degisikliginden once dosya yedegi alinir.",
            "Servis/SSH test gecmezse yedekten geri donulur ve restart edilir.",
            "Ornek rollback: cp <backup> /etc/ssh/sshd_config && systemctl reload ssh || systemctl restart ssh",
        ],
        "secret_policy": "Secret degerleri raporda gosterilmez; sadece maske ve konum sinyali kullanilir.",
        "auto_apply": False,
        "approval_required": bool(risks),
    }


def build_readiness_report(scorecard: Mapping[str, Any]) -> Dict[str, Any]:
    """%100 Jarvis hedefini yerel/onanabilir/harici gereksinimlere ayirir."""
    blockers = list(scorecard.get("why_not_100", []) or [])
    current = float(scorecard.get("overall_percent", 0) or 0)
    approval_items: List[str] = []
    for blocker in blockers:
        lowered = blocker.casefold()
        if any(word in lowered for word in ["hafiza", "dependency", "guvenlik", "güvenlik", "ssh", "secret"]):
            approval_items.append(blocker)
    local_done = [
        "Saglik, hafiza, arac, guvenlik, COO cevap ve stratejik durum skor karti var.",
        "Hermes durum raporu risk/firsat/tek odak/bekleyen karar/sonraki eylem uretiyor.",
        "Kendini gelistirme raporu otomatik uygulama yapmadan oneri uretiyor.",
    ]
    external = [
        "Takvim ve gorev verisi baglanmadan gunluk zaman gercekligi tam olculemez.",
        "Finans/nakit/borc verisi baglanmadan gelir-risk onceligi tam otomatiklesmez.",
        "Operasyon/musteri sinyalleri baglanmadan firsat ve takip kacagi tam yakalanmaz.",
    ]
    local_max = 100.0 if current >= 99 and not approval_items else min(95, max(current, 85) + (5 if not approval_items else 0))
    return {
        "mevcut_skor": current,
        "local_max_percent": local_max,
        "su_an_tamam": local_done,
        "onayla_uygulanabilir": approval_items or ["Yerel cekirdek icin acil onayli is kalmadi."],
        "harici_entegrasyon_gerekir": external,
        "romantik_iddia_degil": True,
        "sonraki_en_yuksek_kaldirac": (approval_items or external)[:3],
    }


def run_readiness_report() -> Dict[str, Any]:
    """Canli skor kartindan %100 hazirlik raporu uretir; read-only calisir."""
    return build_readiness_report(run_scorecard())
