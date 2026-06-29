"""
שמירה וטעינה של משובי משתמש.
כל משוב נשמר כשורת JSON ב-feedback_log.jsonl.
"""
import json
import os
from datetime import datetime

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(_BASE, "feedback_log.jsonl")

REASON_LABELS = {
    "approved":       "השינוי מבורך ✅",
    "worse_rhyme":    "החרוז פחות טוב ❌",
    "bad_context":    "לא מתאים להקשר 🎭",
    "dislike":        "לא אהבתי 👎",
    "other":          "אחר ✏️",
}


def save_feedback(original_word: str, suggested_word: str, reason: str, custom_text: str = "") -> None:
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "original": original_word,
        "suggested": suggested_word,
        "reason": reason,
        "custom": custom_text,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_rejected_words(original_word: str) -> set[str]:
    """מחזיר קבוצת מילים שנדחו בעבר עבור original_word (רק סיבות שאינן approved)."""
    rejected = set()
    if not os.path.exists(LOG_PATH):
        return rejected
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("original") == original_word and entry.get("reason") != "approved":
                    rejected.add(entry["suggested"])
            except json.JSONDecodeError:
                continue
    return rejected
