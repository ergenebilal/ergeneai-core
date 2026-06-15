"""
AI/LLM tools module.
Handles LongTracer model, claim verification, and sentiment analysis.
"""

# === LONGTRACER CACHE ===
_longtracer_model = None


def get_longtracer_model() -> object:
    """Loads and returns the LongTracer model as a singleton.

    Returns:
        object: LongTracer model instance

    Example:
        lt = get_longtracer_model()
        result = lt.check(response="example", sources=["source"])
    """
    global _longtracer_model
    if _longtracer_model is None:
        try:
            import longtracer
            _longtracer_model = longtracer
        except ImportError:
            _longtracer_model = None
    return _longtracer_model


def verify_claim(claim: str, source: str) -> dict:
    """Verifies a claim using LongTracer.

    Args:
        claim: The claim text to verify
        source: Source reference

    Returns:
        dict: {"verdict": "PASS"|"FAIL", "confidence": float|None}
    """
    try:
        lt = get_longtracer_model()
        if lt is None:
            return {"verdict": "UNKNOWN", "confidence": None}
        result = lt.check(response=claim, sources=[source])
        if hasattr(result, 'verdict'):
            return {"verdict": result.verdict, "confidence": getattr(result, 'confidence', None)}
        elif isinstance(result, dict):
            return result
        return {"verdict": "PASS" if result else "FAIL", "confidence": None}
    except Exception as e:
        return {"verdict": "ERROR", "confidence": None, "error": str(e)}


def analyze_sentiment(message: str) -> dict:
    """Performs simple sentiment analysis.

    Args:
        message: Input message text

    Returns:
        dict: {"status": "MUTLU|YORGUN/SINIRLI|NOTR", "score": -1..1, "triggers": []}
    """
    positive_words = ["teşekkür", "harika", "süper", "iyi", "başarılı", "aferin", "mükemmel"]
    negative_words = ["kötü", "hata", "yanlış", "sinir", "yorgun", "bıktım", "yeter", "uğraşma"]
    message_lower = message.lower()

    triggers = []
    score = 0

    for w in positive_words:
        if w in message_lower:
            triggers.append(w)
            score += 0.3
    for w in negative_words:
        if w in message_lower:
            triggers.append(w)
            score -= 0.4

    score = max(-1.0, min(1.0, score))

    if score > 0.2:
        status = "MUTLU"
    elif score < -0.2:
        status = "YORGUN/SINIRLI"
    else:
        status = "NOTR"

    return {"status": status, "score": score, "triggers": triggers}
