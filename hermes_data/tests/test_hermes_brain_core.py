
import ast
import json
from pathlib import Path

import pytest

from hermes_brain_core import (
    ACTION_ALLOW,
    ACTION_APPROVAL_REQUIRED,
    ACTION_FORBID,
    apply_physical_action_plan,
    build_physical_action_plan,
    build_brain_health_report,
    classify_autonomy_action,
    generate_briefing,
    normalize_memory_category,
    rank_priorities,
)


TOOLS_SOURCE = Path(__file__).resolve().parents[1] / "tools.py"


def _tool_function_names():
    tree = ast.parse(TOOLS_SOURCE.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_normalize_memory_category_maps_hermes_brain_labels():
    assert normalize_memory_category("kişisel hatırlatma") == "kisisel"
    assert normalize_memory_category("business_strategy") == "strateji"
    assert normalize_memory_category("tech_note") == "teknik"
    assert normalize_memory_category("müşteri dışı operasyon") == "operasyon"
    assert normalize_memory_category("bilinmeyen") == "genel"


def test_rank_priorities_puts_urgent_revenue_risk_first():
    items = [
        {"baslik": "Logo rengi sec", "aciliyet": 1, "gelir_etkisi": 1, "risk": 1, "kaldirac": 1, "hedef_uyumu": 1},
        {"baslik": "11 Haziran kart son odeme", "aciliyet": 5, "gelir_etkisi": 4, "risk": 5, "kaldirac": 3, "hedef_uyumu": 5},
        {"baslik": "Yeni arac health testi", "aciliyet": 3, "gelir_etkisi": 2, "risk": 4, "kaldirac": 4, "hedef_uyumu": 4},
    ]

    ranked = rank_priorities(items)

    assert ranked[0]["baslik"] == "11 Haziran kart son odeme"
    assert ranked[0]["puan"] > ranked[1]["puan"] > ranked[2]["puan"]
    assert ranked[0]["nedenler"]


def test_classify_autonomy_action_separates_safe_approval_and_forbidden():
    assert classify_autonomy_action("bugunku riskleri analiz et")["sinif"] == ACTION_ALLOW
    assert classify_autonomy_action("hafizaya bu notu kaydet")["sinif"] == ACTION_APPROVAL_REQUIRED
    assert classify_autonomy_action("systemctl restart hermes")["sinif"] == ACTION_APPROVAL_REQUIRED
    assert classify_autonomy_action("veritabani migration calistir")["sinif"] == ACTION_APPROVAL_REQUIRED
    assert classify_autonomy_action("secretleri baska yere tasi")["sinif"] == ACTION_APPROVAL_REQUIRED
    assert classify_autonomy_action("n8n instagram workflowunu degistir")["sinif"] == ACTION_APPROVAL_REQUIRED
    assert classify_autonomy_action(".env dosyasindaki tokeni goster")["sinif"] == ACTION_FORBID
    assert classify_autonomy_action("rm -rf /opt/hermes")["sinif"] == ACTION_FORBID


def test_generate_briefing_returns_operational_sections():
    briefing = generate_briefing(
        memories=[
            {"content": "Denizbank son odeme 11 Haziran", "category": "risk"},
            {"content": "USD odakli mini SaaS hedefi", "category": "strateji"},
            {"content": "Embedding daemon saglikli", "category": "teknik"},
        ],
        health={"overall": "degraded", "broken": ["MCP fetch baglantisi"]},
        mode="sabah",
    )

    assert briefing["mod"] == "sabah"
    assert briefing["riskler"]
    assert briefing["firsatlar"]
    assert briefing["odak"]
    assert "teknik_detay_yok" in briefing["cevap_disiplini"]


def test_generate_briefing_returns_morning_and_evening_operating_fields():
    morning = generate_briefing(
        memories=[
            {"content": "Denizbank son odeme bu hafta; nakit riski yuksek", "category": "risk"},
            {"content": "USD gelir firsati icin premium teklif hazirla", "category": "firsat"},
            {"content": "Embedding daemon saglikli", "category": "teknik"},
        ],
        health={"overall": "degraded", "broken": ["MCP tool"]},
        mode="sabah",
    )
    evening = generate_briefing(
        memories=[
            {"content": "Bugun teklif taslagi ogrenildi ve takip gerekiyor", "category": "firsat"},
            {"content": "Yarina kalan risk nakit planinin netlesmemesi", "category": "risk"},
        ],
        health={"overall": "healthy", "broken": []},
        mode="aksam",
    )

    assert len(morning["en_kritik_3_risk"]) == 3
    assert morning["en_yuksek_gelir_firsati"]
    assert morning["bugunun_tek_odagi"]
    assert morning["bekleyen_kararlar"]
    assert evening["ogrenilenler"]
    assert evening["takip_listesi"]
    assert evening["yarina_kalan_risk"]


def test_build_brain_health_report_summarizes_component_state():
    report = build_brain_health_report([
        {"ad": "Embedding Daemon", "durum": "ok", "detay": "model yuklu"},
        {"ad": "MCP fetch", "durum": "broken", "detay": "connection closed"},
        {"ad": "Root SSH", "durum": "risk", "detay": "password login enabled"},
    ])

    assert report["overall"] == "degraded"
    assert report["counts"] == {"ok": 1, "warn": 0, "broken": 1, "risk": 1, "unknown": 0}
    assert report["broken"] == ["MCP fetch"]
    assert report["risks"] == ["Root SSH"]


def test_tools_exposes_hermes_brain_functions():
    expected = [
        "hermes_beyin_saglik_raporu",
        "hermes_oncelik_analiz",
        "hermes_proaktif_brifing",
        "hermes_eylem_guvenlik_sinifi",
        "hermes_gelisim_raporu",
    ]
    available = _tool_function_names()
    for name in expected:
        assert name in available, name


def test_prepare_memory_entry_adds_quality_metadata_and_normalizes_category():
    from hermes_brain_core import prepare_memory_entry

    entry = prepare_memory_entry(
        "Denizbank kart son odeme 11 Haziran; gecikirse nakit baskisi artar.",
        category="business_strategy",
        importance=5,
        recall_purpose="sabah brifinginde risk olarak hatirlat",
    )

    assert entry["content"].startswith("Denizbank")
    assert entry["category"] == "strateji"
    assert entry["importance"] == 5
    assert entry["recall_purpose"] == "sabah brifinginde risk olarak hatirlat"
    assert entry["quality"]["ready_to_save"] is True
    assert entry["quality"]["warnings"] == []


def test_prepare_memory_entry_flags_weak_entries_before_save():
    from hermes_brain_core import prepare_memory_entry

    entry = prepare_memory_entry("kisa", category="belirsiz", importance=9, recall_purpose="")

    assert entry["category"] == "genel"
    assert entry["importance"] == 5
    assert entry["quality"]["ready_to_save"] is False
    assert "icerik_cok_kisa" in entry["quality"]["warnings"]
    assert "hatirlama_amaci_yok" in entry["quality"]["warnings"]


def test_assess_memory_quality_detects_duplicates_and_category_spread():
    from hermes_brain_core import assess_memory_quality

    report = assess_memory_quality([
        {"content": "Bilal Eylul 2026 kuryelikten cikmak istiyor", "category": "business_strategy"},
        {"content": "Bilal Eylul 2026 kuryelikten cikmak istiyor", "category": "business_strategy"},
        {"content": "Embedding daemon calisiyor", "category": "tech_note"},
        {"content": "", "category": "risk"},
    ])

    assert report["total"] == 4
    assert report["duplicates"] == 1
    assert report["empty"] == 1
    assert report["normalized_categories"]["strateji"] == 2
    assert report["normalized_categories"]["teknik"] == 1
    assert report["quality_score"] < 100
    assert "tekrar_kayit_var" in report["warnings"]


def test_tools_exposes_memory_quality_functions():
    available = _tool_function_names()

    assert "hermes_hafiza_kalite_raporu" in available
    assert "hermes_hafiza_kayit_hazirla" in available


def test_run_command_accepts_environment_for_postgres_helpers():
    import sys
    from hermes_brain_core import _run_command

    code, output = _run_command(
        [sys.executable, "-c", "import os; print(os.environ.get('HERMES_TEST_ENV'))"],
        env={"HERMES_TEST_ENV": "visible"},
    )

    assert code == 0
    assert output.strip() == "visible"


def test_decision_engine_uses_cash_pressure_to_break_priority_ties():
    from hermes_brain_core import make_decision_plan

    tasks = [
        {"baslik": "Kart son odeme tarihini kacirma", "aciliyet": 5, "gelir_etkisi": 3, "risk": 5, "kaldirac": 2, "hedef_uyumu": 5},
        {"baslik": "Yeni gelir firsati icin teklif hazirla", "aciliyet": 4, "gelir_etkisi": 5, "risk": 2, "kaldirac": 5, "hedef_uyumu": 5},
    ]

    plan = make_decision_plan(tasks, context={"nakit_baskisi": True, "hedef": "Eylul 2026 kuryelikten cikmak"})

    assert plan["tek_odak"]["baslik"] == "Kart son odeme tarihini kacirma"
    assert plan["tek_odak"]["karar_tipi"] == "risk_koruma"
    assert plan["sonraki_eylem"]
    assert "nakit baskisi" in " ".join(plan["tek_odak"]["nedenler"])


def test_decision_engine_prioritizes_revenue_when_growth_mode_without_cash_pressure():
    from hermes_brain_core import make_decision_plan

    tasks = [
        {"baslik": "Kart son odeme tarihini kacirma", "aciliyet": 3, "gelir_etkisi": 2, "risk": 4, "kaldirac": 2, "hedef_uyumu": 4},
        {"baslik": "USD gelir firsati icin premium teklif hazirla", "aciliyet": 4, "gelir_etkisi": 5, "risk": 2, "kaldirac": 5, "hedef_uyumu": 5},
    ]

    plan = make_decision_plan(tasks, context={"nakit_baskisi": False, "buyume_modu": True})

    assert plan["tek_odak"]["baslik"] == "USD gelir firsati icin premium teklif hazirla"
    assert plan["tek_odak"]["karar_tipi"] == "gelir_kaldiraci"
    assert plan["bekleyen_kararlar"] == []


def test_decision_engine_flags_missing_scores_as_pending_decisions():
    from hermes_brain_core import make_decision_plan

    plan = make_decision_plan([{"baslik": "Belirsiz hedef"}], context={})

    assert plan["bekleyen_kararlar"]
    assert "puanlama_eksik" in plan["bekleyen_kararlar"][0]


def test_operational_priority_engine_extracts_evening_report_focus():
    from hermes_brain_core import build_operational_priority

    report = """
    Durum Raporu — 2 Haziran 2026 Akşam
    Risk Radarı:
    - 11 Haz — Denizbank asgari 9.000₺ (9 gün)
    - 14 Haz — Motor sigortası bitiyor (12 gün) — dosya hala açık
    Fırsat:
    - Balık restoranı sıcak müşteri — bu hafta kapatılırsa referans zinciri başlar
    Hedef: Eylül 2026 — kuryelik biter, OtelAI düzenli gelir getirir.
    """

    result = build_operational_priority(report, reference_date="2026-06-02")

    assert "balik restorani" in result["bugunun_tek_odagi"].casefold()
    assert "Denizbank" in " ".join(result["risk_korumalari"])
    assert "Motor sigortasi" in " ".join(result["risk_korumalari"])
    assert "OtelAI" in result["hedef_uyumu"]
    assert any("referans zinciri" in reason for reason in result["neden_bu_odak"])
    assert result["ilk_somut_adim"]


def test_operational_priority_engine_overrides_with_imminent_payment_risk():
    from hermes_brain_core import build_operational_priority

    report = """
    Risk Radarı:
    - 4 Haz — Denizbank asgari 9.000₺ (2 gün)
    Fırsat:
    - Balık restoranı sıcak müşteri — bu hafta kapatılırsa referans zinciri başlar
    Hedef: Eylül 2026 — kuryelik biter, OtelAI düzenli gelir getirir.
    """

    result = build_operational_priority(report, reference_date="2026-06-02")

    assert "Denizbank" in result["bugunun_tek_odagi"]
    assert result["sirali_oncelikler"][0]["karar_tipi"] == "risk_koruma"
    assert any("0-3 gun" in reason or "yaklasan risk" in reason for reason in result["neden_bu_odak"])


def test_operational_priority_engine_prefers_hot_customer_when_risk_not_imminent():
    from hermes_brain_core import build_operational_priority

    report = """
    Risk Radarı:
    - 20 Haz — Motor sigortası bitiyor (18 gün)
    Fırsat:
    - Balık restoranı sıcak müşteri — bu hafta kapatılırsa referans zinciri başlar
    Hedef: Eylül 2026 — kuryelik biter, OtelAI düzenli gelir getirir.
    """

    result = build_operational_priority(report, reference_date="2026-06-02")

    assert "balik restorani" in result["bugunun_tek_odagi"].casefold()
    assert result["gelir_firsati"]
    assert result["sirali_oncelikler"][0]["karar_tipi"] == "gelir_kaldiraci"


def test_operational_priority_engine_flags_ambiguous_task_data():
    from hermes_brain_core import build_operational_priority

    result = build_operational_priority("Belirsiz hedef: dosya açık, tarih ve tutar net değil.", reference_date="2026-06-02")

    assert result["bekleyen_kararlar"]
    assert any("tarih" in item.casefold() or "tutar" in item.casefold() for item in result["bekleyen_kararlar"])


def test_tools_exposes_decision_plan_function():
    available = _tool_function_names()

    assert "hermes_karar_plani" in available
    assert "hermes_oncelik_motoru" in available


def test_tool_reliability_report_marks_missing_dependency_tools():
    from hermes_brain_core import build_tool_reliability_report

    report = build_tool_reliability_report(
        functions=["pg_baglan", "pg_ara", "terminal_calistir", "web_cek"],
        dependency_checks={"psycopg2": False, "requests": True},
    )

    assert report["total_tools"] == 4
    assert report["usable_tools"] == 2
    assert report["availability_percent"] == 50.0
    assert report["tools"]["pg_baglan"]["status"] == "blocked"
    assert "psycopg2" in report["tools"]["pg_baglan"]["missing_dependencies"]
    assert report["tools"]["terminal_calistir"]["risk"] == "approval_required"


def test_tool_reliability_report_recommends_safe_fallbacks():
    from hermes_brain_core import build_tool_reliability_report

    report = build_tool_reliability_report(
        functions=["pg_ara_vector", "beyin_ara"],
        dependency_checks={"psycopg2": False, "sentence_transformers": False, "chromadb": True},
    )

    assert report["tools"]["pg_ara_vector"]["fallback"] == "hermes_hafiza_kalite_raporu"
    assert report["tools"]["beyin_ara"]["status"] == "usable"
    assert report["summary"]["blocked"] == 1


def test_tools_exposes_tool_reliability_report():
    available = _tool_function_names()

    assert "hermes_arac_guvenilirlik_raporu" in available


def test_coo_response_quality_scores_strategic_operating_discipline():
    from hermes_brain_core import evaluate_coo_response_quality

    strong = evaluate_coo_response_quality(
        scenario="para_borc_baskisi",
        response=(
            "En kritik risk nakit ve borc baskisi. Bugunun tek odagi Denizbank son odeme "
            "riskini kapatmak. Gelir etkisi icin USD teklifini yarina hazirla. Sonraki eylem: "
            "bugun 30 dakika icinde odeme tutari, son tarih ve eksik nakdi netlestir. "
            "Servis restart veya secret tasima icin onay gerekir."
        ),
    )
    weak = evaluate_coo_response_quality(
        scenario="para_borc_baskisi",
        response="Merak etme, her sey yoluna girer. Bir liste yapip sakin kalmani oneririm.",
    )

    assert strong["score"] >= 80
    assert strong["passed"] is True
    assert weak["score"] < 50
    assert weak["passed"] is False
    assert "tek_sonraki_eylem" in strong["matched_criteria"]


def test_tools_exposes_coo_response_quality_report():
    available = _tool_function_names()

    assert "hermes_coo_cevap_kalite_raporu" in available


def test_coo_quality_report_compares_before_after_for_all_scenarios():
    from hermes_brain_core import COO_SCENARIOS, run_coo_response_quality_report

    baseline = {
        scenario: "Bunu dusunup bir liste yapmak iyi olur."
        for scenario in COO_SCENARIOS
    }
    improved = {
        "para_borc_baskisi": "Bilal icin en kritik risk nakit ve borc baskisi. Bugunun tek odagi son odeme riskini kapatmak. Neden: gecikme zaman ve gelir odagini bozar. Sonraki eylem: bugun tutar ve tarihi netlestir. Secret veya restart icin onay gerekir.",
        "gelir_firsati": "Bilal icin gelir firsati USD teklifidir. Bugunun tek odagi yuksek kaldiracli teklifi cikarmak. Neden: zaman kaybi gelir riskini artirir. Sonraki eylem: ilk somut adim olarak teklif basliklarini yaz. Riskli eylemde onay gerekir.",
        "teknik_hata": "Bilal icin teknik hata gelir ve risk etkisine gore siralanmali. Bugunun tek odagi servis riskini izole etmek. Neden: zaman kaybi operasyonu bozar. Sonraki eylem: ilk somut adim olarak hatayi tekrar uret. Restart icin onay gerekir.",
        "musteri_operasyonu": "Bilal icin musteri operasyonunda gelir, risk ve zaman birlikte dusunulmeli. Bugunun tek odagi tekrar eden aksakligi kapatmak. Neden: operasyon kaybi gelir riskidir. Sonraki eylem: ilk somut adim olarak takip listesini netlestir. Secret icin onay gerekir.",
        "zaman_onceligi": "Bilal icin zaman riski en kritik konu. Bugunun tek odagi tek is secmek ve digerlerini ertelemek. Neden: daginik odak gelir kaybina yol acar. Sonraki eylem: ilk somut adim olarak 60 dakikalik blok ayir. Riskli eylemde onay gerekir.",
        "riskli_eylem_talebi": "Bilal icin bu riskli eylem onay gerekir sinifinda. Bugunun tek odagi zarari onlemek. Neden: restart veya secret islemi gelir ve zaman riskidir. Sonraki eylem: ilk somut adim olarak etki ve geri alma planini yaz. Yasak durum varsa dur.",
        "belirsiz_hedef": "Bilal icin belirsiz hedef gelir, risk ve zaman olarak netlesmeli. Bugunun tek odagi tek olculebilir hedef secmek. Neden: belirsizlik odak kaybi yaratir. Sonraki eylem: ilk somut adim olarak hedefi tarih ve tutarla yaz. Onay gerekir eylemleri ayir.",
    }

    report = run_coo_response_quality_report(samples=improved, baseline_samples=baseline)

    assert report["provided_samples"] == len(COO_SCENARIOS)
    assert report["pass_count"] == len(COO_SCENARIOS)
    assert report["average_score"] >= 75
    assert report["comparison"]["after_average"] > report["comparison"]["before_average"]
    assert report["scenarios"]["riskli_eylem_talebi"]["passed"] is True


def test_development_report_proposes_improvements_without_auto_applying():
    from hermes_brain_core import ACTION_APPROVAL_REQUIRED, ACTION_FORBID, build_development_report

    report = build_development_report({
        "overall": "degraded",
        "broken": ["MCP fetch"],
        "risks": ["Root SSH"],
        "warnings": ["tools.py dependency"],
    })

    assert report["hata_analizi"]
    assert report["gelisim_onerileri"]
    assert report["test_onerileri"]
    assert report["patch_plani"]
    assert report["risk_raporu"]
    assert report["otomatik_uygulama"] is False
    assert report["guvenlik_siniri"]["izin_verilenler"]
    assert report["guvenlik_siniri"]["yasak_veya_onay_gerektirenler"]
    assert report["eylem_siniflari"]["canli_prompt_degistirme"] == ACTION_APPROVAL_REQUIRED
    assert report["eylem_siniflari"]["secret_gosterme"] == ACTION_FORBID


def test_strategic_operating_status_returns_jarvis_like_focus_fields():
    from hermes_brain_core import build_strategic_status

    status = build_strategic_status(
        memories=[
            {"content": "Denizbank son odeme bu hafta; nakit riski yuksek", "category": "risk"},
            {"content": "USD gelir firsati icin premium teklif hazirla", "category": "firsat"},
            {"content": "Teknik borc: MCP baglantisi izlenmeli", "category": "teknik"},
        ],
        health={"overall": "degraded", "broken": ["Embedding daemon latency"], "risks": ["Root SSH"]},
        tasks=[
            {"baslik": "Kart son odeme tarihini kacirma", "aciliyet": 5, "gelir_etkisi": 3, "risk": 5, "kaldirac": 2, "hedef_uyumu": 5},
            {"baslik": "USD gelir firsati icin premium teklif hazirla", "aciliyet": 4, "gelir_etkisi": 5, "risk": 2, "kaldirac": 5, "hedef_uyumu": 5},
        ],
        context={"nakit_baskisi": True},
    )

    assert len(status["en_kritik_3_risk"]) == 3
    assert status["en_yuksek_gelir_firsati"]
    assert status["bugunun_tek_odak_konusu"] == "Kart son odeme tarihini kacirma"
    assert status["bu_hafta_yapilmazsa_zarar_verecek_konu"]
    assert status["bekleyen_kararlar"]
    assert status["onerilen_sonraki_eylem"]
    assert status["soru"] == "Bilal su an neyi kaciriyor?"


def test_tools_exposes_hermes_durum():
    available = _tool_function_names()

    assert "hermes_durum" in available


def test_scorecard_explains_why_hermes_is_not_100_percent():
    from hermes_brain_core import build_scorecard

    scorecard = build_scorecard(
        health={"overall": "degraded"},
        memory_quality={"quality_score": 73, "warnings": ["hatirlama_amaci_eksik"]},
        tool_reliability={"availability_percent": 78.8, "missing_dependencies": ["psycopg2"]},
        security_report={"risk_count": 2, "risks": [{"ad": "Root SSH"}, {"ad": ".env secrets"}]},
        strategic_status={"bugunun_tek_odak_konusu": "Kart son odeme tarihini kacirma"},
        coo_quality={"average_score": 100, "pass_count": 7, "scenario_count": 7},
        log_health={"warning_count": 0, "error_count": 0},
    )

    assert scorecard["overall_percent"] < 100
    assert scorecard["grade"] in {"80", "90"}
    assert "hafiza" in scorecard["metrics"]
    assert "araclar" in scorecard["metrics"]
    assert scorecard["why_not_100"]
    assert any("hatirlama_amaci_eksik" in item for item in scorecard["why_not_100"])
    assert scorecard["next_leverage"]


def test_run_scorecard_uses_coo_capability_baseline_instead_of_empty_samples():
    from hermes_brain_core import run_scorecard

    scorecard = run_scorecard()

    assert scorecard["metrics"]["coo_cevap"] >= 75
    assert scorecard["grade"] in {"80", "90", "100"}


def test_tools_exposes_scorecard():
    available = _tool_function_names()

    assert "hermes_skor_karti" in available


def test_memory_surgery_plan_fixes_missing_recall_purpose_without_writing():
    from hermes_brain_core import build_memory_surgery_plan

    plan = build_memory_surgery_plan([
        {"id": 1, "content": "Denizbank son odeme bu hafta; nakit riski yuksek", "category": "genel"},
        {"id": 2, "content": "USD gelir firsati icin premium teklif hazirla", "category": "business_strategy"},
    ])

    assert plan["current_quality"]["warnings"]
    assert plan["target_quality_score"] >= 90
    assert plan["auto_write"] is False
    assert plan["approval_required"] is True
    assert len(plan["proposed_updates"]) == 2
    assert all(update["recall_purpose"] for update in plan["proposed_updates"])
    assert all(update["category"] in {"risk", "firsat", "strateji", "teknik", "operasyon", "is", "kisisel", "genel"} for update in plan["proposed_updates"])
    assert plan["import_plan"]


def test_collect_postgres_memory_records_reads_annotation_metadata(monkeypatch):
    import hermes_brain_core

    calls = []

    def fake_run_command(args, timeout=20, env=None):
        calls.append(" ".join(args))
        if "to_regclass" in args[-1]:
            return 0, "t\n"
        return 0, "7|Nakit riski|risk|2026-06-02|sabah brifinginde risk olarak hatirlat|5\n"

    monkeypatch.setattr(hermes_brain_core, "_run_command", fake_run_command)

    records = hermes_brain_core.collect_postgres_memory_records(limit=1)

    assert records[0]["recall_purpose"] == "sabah brifinginde risk olarak hatirlat"
    assert records[0]["importance"] == "5"
    assert "hermes_memory_annotations" in calls[1]


def test_tools_exposes_memory_surgery_plan():
    available = _tool_function_names()

    assert "hermes_hafiza_ameliyat_plani" in available


def test_tool_surgery_plan_maps_missing_dependencies_to_actions_without_installing():
    from hermes_brain_core import build_tool_surgery_plan

    plan = build_tool_surgery_plan(
        functions=["pg_baglan", "pg_ara_vector", "beyin_ara", "terminal_calistir"],
        dependency_checks={"psycopg2": False, "sentence_transformers": False, "chromadb": True},
    )

    assert plan["auto_install"] is False
    assert plan["approval_required"] is True
    assert plan["target_availability_percent"] >= 90
    assert plan["actions"]["pg_baglan"]["decision"] == "blocked"
    assert plan["actions"]["pg_ara_vector"]["decision"] == "use_fallback"
    assert plan["actions"]["pg_ara_vector"]["fallback"] == "hermes_hafiza_kalite_raporu"
    assert plan["actions"]["terminal_calistir"]["decision"] == "approval_required"
    assert plan["dependency_plan"]["psycopg2"]["approval_required"] is True


def test_tools_exposes_tool_surgery_plan():
    available = _tool_function_names()

    assert "hermes_arac_ameliyat_plani" in available


def test_security_hardening_plan_masks_secrets_and_requires_approval():
    from hermes_brain_core import build_security_hardening_plan

    plan = build_security_hardening_plan({
        "root_ssh": True,
        "password_auth": True,
        "env_files": ["/opt/hermes/.env"],
        "open_ports": [22, 8642],
        "service_user": "hermes",
        "secret_samples": ["SUPER_SECRET_VALUE"],
    })

    assert plan["auto_apply"] is False
    assert plan["approval_required"] is True
    assert plan["risk_count"] >= 4
    assert "SUPER_SECRET_VALUE" not in str(plan)
    assert plan["rollback_plan"]
    assert plan["approval_gate"]["second_session_required"] is True
    assert plan["approval_gate"]["admin_key_verified"] is False
    assert plan["implementation_plan"]
    assert any(item["risk"] == "root_ssh" for item in plan["risk_matrix"])
    assert any(item["risk"] == "env_secret_hygiene" for item in plan["risk_matrix"])


def test_parse_ssh_security_policy_treats_root_no_and_password_no_as_safe():
    from hermes_brain_core import parse_ssh_security_policy

    safe = parse_ssh_security_policy("permitrootlogin no\npasswordauthentication no\n")
    risky = parse_ssh_security_policy("permitrootlogin yes\npasswordauthentication yes\n")

    assert safe == {"root_ssh": False, "password_auth": False}
    assert risky == {"root_ssh": True, "password_auth": True}


def test_collect_ssh_policy_output_falls_back_to_readable_config(monkeypatch):
    import hermes_brain_core

    def fake_run_command(args, timeout=10, env=None):
        if args[:2] == ["sshd", "-T"]:
            return 255, "sshd: no hostkeys available"
        return 0, "PermitRootLogin no\nPasswordAuthentication no\n"

    monkeypatch.setattr(hermes_brain_core, "_run_command", fake_run_command)

    output = hermes_brain_core.collect_ssh_policy_output()

    assert "PermitRootLogin no" in output
    assert hermes_brain_core.parse_ssh_security_policy(output) == {"root_ssh": False, "password_auth": False}


def test_tools_exposes_security_hardening_plan():
    available = _tool_function_names()

    assert "hermes_guvenlik_sertlestirme_plani" in available


def test_strategic_status_includes_scorecard_based_reasoning():
    from hermes_brain_core import build_strategic_status

    status = build_strategic_status(
        memories=[{"content": "Nakit riski ve USD gelir firsati ayni anda izlenmeli", "category": "risk"}],
        health={"overall": "degraded", "broken": [], "risks": ["Root SSH"]},
        tasks=[
            {"baslik": "Nakit riskini kapat", "aciliyet": 5, "gelir_etkisi": 3, "risk": 5, "kaldirac": 2, "hedef_uyumu": 5},
            {"baslik": "USD teklif hazirla", "aciliyet": 4, "gelir_etkisi": 5, "risk": 2, "kaldirac": 5, "hedef_uyumu": 5},
        ],
        context={"nakit_baskisi": True},
        scorecard={"metrics": {"hafiza": 73, "araclar": 78, "guvenlik": 60}, "why_not_100": ["Hafiza kalite uyarisi"]},
    )

    assert status["skor_karti"]["metrics"]["hafiza"] == 73
    assert status["neden_bu_odak"]
    assert status["neden_digerleri_bekliyor"]
    assert "guvenlik" in status["denge_sinyalleri"]
    assert "Hafiza kalite uyarisi" in status["yuzde_100_engelleri"]


def test_readiness_report_separates_local_done_approval_and_external_needs():
    from hermes_brain_core import build_readiness_report

    report = build_readiness_report({
        "overall_percent": 84,
        "why_not_100": ["Hafiza kalite uyarisi", "Arac dependency eksik: psycopg2", "Guvenlik riski: Root SSH"],
        "metrics": {"hafiza": 73, "araclar": 78, "guvenlik": 60},
    })

    assert report["local_max_percent"] >= 85
    assert report["su_an_tamam"]
    assert report["onayla_uygulanabilir"]
    assert report["harici_entegrasyon_gerekir"]
    assert report["romantik_iddia_degil"] is True
    assert any("hafiza" in item.casefold() for item in report["onayla_uygulanabilir"])
    assert any("takvim" in item.casefold() or "finans" in item.casefold() for item in report["harici_entegrasyon_gerekir"])


def test_readiness_report_allows_local_100_when_scorecard_has_no_blockers():
    from hermes_brain_core import build_readiness_report

    report = build_readiness_report({
        "overall_percent": 100,
        "why_not_100": [],
        "metrics": {"hafiza": 100, "araclar": 100, "guvenlik": 100},
    })

    assert report["local_max_percent"] == 100.0
    assert report["onayla_uygulanabilir"] == ["Yerel cekirdek icin acil onayli is kalmadi."]


def test_tools_exposes_readiness_report():
    available = _tool_function_names()

    assert "hermes_yuzde_yuz_hazirlik_raporu" in available


def test_build_tts_request_normalizes_text_and_uses_supported_voice():
    from hermes_brain_core import build_tts_request

    request = build_tts_request("  Hermes konuşmaya hazır.  ", voice="marin", response_format="mp3")

    assert request["url"] == "https://api.openai.com/v1/audio/speech"
    assert request["payload"]["model"] == "gpt-4o-mini-tts"
    assert request["payload"]["voice"] == "marin"
    assert request["payload"]["input"] == "Hermes konuşmaya hazır."
    assert request["extension"] == "mp3"


def test_build_tts_request_rejects_empty_text_and_unknown_voice():
    from hermes_brain_core import build_tts_request

    assert build_tts_request("   ")["ok"] is False
    assert "metin_bos" in build_tts_request("   ")["warnings"]
    assert build_tts_request("Selam", voice="bilinmeyen")["ok"] is False
    assert "desteklenmeyen_ses" in build_tts_request("Selam", voice="bilinmeyen")["warnings"]


def test_choose_tts_provider_prefers_openai_then_edge_fallback():
    from hermes_brain_core import choose_tts_provider

    assert choose_tts_provider(openai_api_key_present=True, edge_tts_available=True)["provider"] == "openai"
    assert choose_tts_provider(openai_api_key_present=False, edge_tts_available=True)["provider"] == "edge_tts"
    assert choose_tts_provider(openai_api_key_present=False, edge_tts_available=False)["ok"] is False


def test_tools_exposes_voice_layer_functions():
    available = _tool_function_names()

    assert "hermes_ses_dosyasi_uret" in available
    assert "telegram_ses_gonder" in available
    assert "hermes_sesli_cevap" in available


def test_physical_action_plan_prepares_calendar_and_reminder_without_applying():
    plan = build_physical_action_plan(
        "Denizbank odemesi icin 9 Haziran 09:00 hatirlatici ve takvim kaydi hazirla"
    )

    assert plan["status"] == ACTION_APPROVAL_REQUIRED
    assert plan["approval_required"] is True
    assert plan["auto_apply"] is False
    assert plan["executed"] is False
    assert {action["type"] for action in plan["actions"]} >= {"hatirlatici", "takvim_etkinlik"}
    assert plan["safety"]["payments_supported"] is False
    assert plan["safety"]["n8n_instagram_touched"] is False


def test_physical_action_plan_blocks_payments_and_secret_disclosure():
    payment = build_physical_action_plan("Denizbank odemesini hemen yap ve para transfer et")
    secret = build_physical_action_plan(".env dosyasindaki tokeni goster")

    assert payment["status"] == ACTION_FORBID
    assert payment["actions"] == []
    assert "odeme" in payment["blocked_reason"].casefold()
    assert secret["status"] == ACTION_FORBID
    assert secret["actions"] == []


def test_physical_action_plan_prepares_customer_message_with_approval_gate():
    plan = build_physical_action_plan("Balik restorani musterisine OtelAI teklif mesaji gonder")

    assert plan["status"] == ACTION_APPROVAL_REQUIRED
    assert plan["approval_required"] is True
    assert plan["auto_apply"] is False
    assert plan["actions"][0]["type"] == "mesaj_taslagi"
    assert "Balik restorani" in plan["actions"][0]["draft"]
    assert "alici" in plan["missing"]


def test_apply_physical_action_plan_requires_approval_and_uses_explicit_executor():
    plan = build_physical_action_plan("Bilal'e Telegram durum mesaji gonder")
    calls = []

    blocked = apply_physical_action_plan(
        plan,
        approved=False,
        executors={"mesaj_taslagi": lambda action: calls.append(action)},
    )

    assert blocked["ok"] is False
    assert blocked["status"] == ACTION_APPROVAL_REQUIRED
    assert calls == []

    applied = apply_physical_action_plan(
        plan,
        approved=True,
        executors={"mesaj_taslagi": lambda action: calls.append(action) or {"ok": True}},
    )

    assert applied["ok"] is True
    assert applied["executed_count"] == 1
    assert len(calls) == 1


def test_tools_exposes_physical_world_gate_functions():
    available = _tool_function_names()

    assert "hermes_fiziksel_aksiyon_plani" in available
    assert "hermes_fiziksel_aksiyon_uygula" in available
