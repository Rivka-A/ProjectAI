"""
שירות למידה מתגמול (RLHF-lite).

מנתח את היסטוריית המשובים ומייצר שני סוגי ידע:

1. learned_level_penalties — רמות חרוז שהמשתמש דחה תכופות.
   למשל: אם רמה 2 נדחית ב-70% מהמקרים → המערכת תדרוש רמה 1 בלבד.

2. learned_key_penalties — זוגות (target_key, suggested_key) שנדחו.
   למשל: אם "עַ" מול "אַ" נדחה 3+ פעמים → הצמד הזה ייחשב כלא-חרוז.

3. learned_context_issues — מילים שנדחו בסיבת "לא מתאים להקשר"
   (לא נוגע לאיכות החרוז עצמו אלא לאוצר המילים).

4. custom_text_insights — תקצירים חוזרים מהשדה "אחר".
"""
import json
import os
from collections import Counter, defaultdict

from services.feedback_service import load_all_feedback, RHYME_QUALITY_REASONS

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEARNED_PATH = os.path.join(_BASE, "learned_rules.json")

# סף מינימלי לדחיות לפני שנלמד כלל
MIN_REJECTIONS = 2
# אחוז דחיות מינימלי מסך ההצגות
MIN_REJECTION_RATE = 0.5


def analyze_and_save() -> dict:
    """
    קורא את כל המשובים, מנתח דפוסים, ושומר כללים ל-learned_rules.json.
    מחזיר את הכללים שנלמדו.
    """
    entries = load_all_feedback()
    if not entries:
        return {}

    # ספירת הצגות ודחיות לפי רמת חרוז
    level_shown:    Counter = Counter()
    level_rejected: Counter = Counter()

    # ספירת הצגות ודחיות לפי זוג מפתחות
    pair_shown:    Counter = Counter()
    pair_rejected: Counter = Counter()

    # מילים שנדחו בגלל הקשר
    context_rejected: Counter = Counter()

    # טקסטים חופשיים מ"אחר"
    custom_texts: list[str] = []

    for e in entries:
        reason = e.get("reason", "")
        level  = e.get("rhyme_level", 0)
        tkey   = e.get("target_key", "")
        skey   = e.get("suggested_key", "")
        suggested = e.get("suggested", "")

        if level:
            level_shown[level] += 1
        if tkey and skey:
            pair_shown[(tkey, skey)] += 1

        if reason == "approved":
            continue

        # דחיות שנוגעות לאיכות החרוז
        if reason in RHYME_QUALITY_REASONS:
            if level:
                level_rejected[level] += 1
            if tkey and skey:
                pair_rejected[(tkey, skey)] += 1

        # דחיות הקשר
        if reason == "bad_context" and suggested:
            context_rejected[suggested] += 1

        # טקסט חופשי
        if reason == "other" and e.get("custom", "").strip():
            custom_texts.append(e["custom"].strip())

    # --- בניית כללים ---

    # רמות חרוז בעייתיות
    bad_levels = []
    for level, rejected in level_rejected.items():
        shown = level_shown.get(level, 0)
        if rejected >= MIN_REJECTIONS and shown > 0 and rejected / shown >= MIN_REJECTION_RATE:
            bad_levels.append(level)

    # זוגות מפתחות בעייתיים
    bad_pairs = []
    for (tk, sk), rejected in pair_rejected.items():
        shown = pair_shown.get((tk, sk), 0)
        if rejected >= MIN_REJECTIONS and shown > 0 and rejected / shown >= MIN_REJECTION_RATE:
            bad_pairs.append([tk, sk])

    # מילים בעייתיות מבחינת הקשר
    context_words = [w for w, cnt in context_rejected.items() if cnt >= MIN_REJECTIONS]

    # תמצות טקסטים חופשיים (קבץ לפי מילות מפתח חוזרות)
    word_freq: Counter = Counter()
    for text in custom_texts:
        for word in text.split():
            if len(word) >= 3:
                word_freq[word] += 1
    frequent_custom_words = [w for w, cnt in word_freq.most_common(10) if cnt >= 2]

    rules = {
        "bad_rhyme_levels": bad_levels,
        "bad_key_pairs": bad_pairs,
        "context_rejected_words": context_words,
        "frequent_custom_keywords": frequent_custom_words,
        "total_feedback": len(entries),
        "approval_rate": round(
            sum(1 for e in entries if e.get("reason") == "approved") / len(entries), 2
        ),
    }

    with open(LEARNED_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    return rules


def load_rules() -> dict:
    """טוען את הכללים הנלמדים מהקובץ."""
    if not os.path.exists(LEARNED_PATH):
        return {}
    with open(LEARNED_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_min_acceptable_level() -> int:
    """
    מחזיר את רמת החרוז המינימלית שהמשתמש מקבל.
    אם רמה 2 נדחית → דרוש רמה 1 בלבד.
    אם רמה 3 נדחית → דרוש לפחות רמה 2.
    ברירת מחדל: רמה 3 (מקובל).
    """
    rules = load_rules()
    bad = set(rules.get("bad_rhyme_levels", []))
    for level in [2, 3, 4]:
        if level in bad:
            return level - 1
    return 3


def is_bad_pair(target_key: str, suggested_key: str) -> bool:
    """מחזיר True אם זוג המפתחות הזה נדחה מספיק פעמים."""
    rules = load_rules()
    return [target_key, suggested_key] in rules.get("bad_key_pairs", [])
