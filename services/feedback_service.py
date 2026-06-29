"""
שמירה וטעינה של משובי משתמש.
כל משוב נשמר כשורת JSON ב-feedback_log.jsonl.
כולל מפתחות החרוז ורמה — לצורך למידה.
"""
import json
import os
from datetime import datetime

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(_BASE, "feedback_log.jsonl")

REASON_LABELS = {
    "approved":    "השינוי מבורך ✅",
    "worse_rhyme": "החרוז פחות טוב ❌",
    "bad_context": "לא מתאים להקשר 🎭",
    "dislike":     "לא אהבתי 👎",
    "other":       "אחר ✏️",
}

# סיבות שמשמעותן שהחרוז עצמו בעייתי (להבדיל מהקשר)
RHYME_QUALITY_REASONS = {"worse_rhyme", "dislike"}


def save_feedback(
    original_word: str,
    suggested_word: str,
    reason: str,
    custom_text: str = "",
    target_key: str = "",
    suggested_key: str = "",
    rhyme_level: int = 0,
) -> None:
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "original": original_word,
        "suggested": suggested_word,
        "reason": reason,
        "custom": custom_text,
        "target_key": target_key,
        "suggested_key": suggested_key,
        "rhyme_level": rhyme_level,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_all_feedback() -> list[dict]:
    if not os.path.exists(LOG_PATH):
        return []
    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def get_rejected_words(original_word: str) -> set[str]:
    """מחזיר קבוצת מילים שנדחו בעבר עבור original_word."""
    rejected = set()
    for entry in load_all_feedback():
        if entry.get("original") == original_word and entry.get("reason") != "approved":
            rejected.add(entry["suggested"])
    return rejected
