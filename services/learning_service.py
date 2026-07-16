# """
# שירות למידה מתגמול (RLHF-lite) עם הגנות מפני הטיה/מניפולציה של משתמש בודד.

# עקרונות מרכזיים (בעקבות עדכון הלוגיקה):

# 1. רק משוב שסווג כ"soft" (services.feedback_service) תורם ללמידה גלובלית
#    (רמות/זוגות חרוז בעייתיים). משוב "hard" (לא מתאים להקשר) ו-"harsh"
#    ("אחר" שלא זוהה כקשור לחרוז) פוסלים רק את ההצעה הבודדת - הם *לעולם*
#    לא מוכללים לכלל שפוסל רמת/זוג חרוז שלמים, כי הם לא נוגעים לאיכות
#    החרוז עצמה.

# 2. "אישרתי" (approved) הוא איתות חיובי שמקוזז מול דחיות: רמה/זוג עם הרבה
#    אישורים לא ייפסלו בקלות בגלל מיעוט "לא אהבתי" מקריים.

# 3. הגנה מפני מניפולציה של משתמש בודד: כלל גלובלי (רמה בעייתית / זוג
#    בעייתי) נלמד רק אם:
#      - יש לפחות MIN_REJECTIONS דחיות מוחלטות, וגם
#      - הן מגיעות מלפחות MIN_DISTINCT_WORDS מילים מקוריות *שונות*
#        (כדי שספאם של אותה מילה לא "יפיל" רמת חרוז שלמה), וגם
#      - שיעור הדחייה נטו (דחיות פחות אישורים, יחסית להצגות) עובר סף גבוה.

# 4. הנתונים הנשמרים לכל זוג הם "אותיות + ניקוד" (המילה המנוקדת בפועל) +
#    רמת החרוז שקבע RhymeChecker - לא ייצוג פונמה מופשט. זה גם מתקן באג
#    ישן שבו אותו זוג נשמר בשני ייצוגי-tuple שונים (list-of-lists מול
#    tuple-of-tuples) כי מקורות שונים בקוד ייצרו אותו מפתח בפורמט שונה.
# """
# import json
# import os
# from collections import Counter, defaultdict

# from services.feedback_service import load_all_feedback
# from core.rhyme_checker import RhymeChecker

# _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# LEARNED_PATH = os.path.join(_BASE, "learned_rules.json")

# # --- ספי הגנה מפני מניפולציה ---
# MIN_REJECTIONS = 3           # מספר דחיות מוחלט מינימלי לפני שנלמד כלל
# MIN_DISTINCT_WORDS = 2       # מס' מילים מקוריות *שונות* שתרמו לדחייה (הגנת גיוון)
# MIN_NET_REJECTION_RATE = 0.6 # (דחיות-אישורים)/הצגות מינימלי כדי לפסול רמה/זוג


# def _canonical_key(vocalized: str, stress: str):
#     """בונה מפתח חרוז קנוני (tuple) מתוך אותיות+ניקוד, לצורך קיבוץ סטטיסטי
#     בלבד. הנתון הנשמר בפועל בקובץ הכללים נשאר אותיות+ניקוד קריאות."""
#     if not vocalized or not stress:
#         return None
#     try:
#         return RhymeChecker.extract_rhyme_key(vocalized, stress)
#     except Exception:
#         return None


# def analyze_and_save() -> dict:
#     """
#     קורא את כל המשובים, מנתח דפוסים תוך הגנה מפני מניפולציה, ושומר כללים
#     ל-learned_rules.json. מחזיר את הכללים שנלמדו.
#     """
#     entries = load_all_feedback()
#     if not entries:
#         return {}

#     level_shown, level_rejected, level_approved = Counter(), Counter(), Counter()
#     pair_shown, pair_rejected, pair_approved = Counter(), Counter(), Counter()
#     level_words: dict[int, set] = defaultdict(set)
#     pair_words: dict[tuple, set] = defaultdict(set)
#     pair_display: dict[tuple, tuple] = {}

#     context_rejected: Counter = Counter()
#     custom_texts: list[str] = []

#     for e in entries:
#         reason = e.get("reason", "")
#         severity = e.get("severity") or ""
#         level = e.get("rhyme_level", 0)
#         original = e.get("original", "")
#         suggested = e.get("suggested", "")

#         okey = _canonical_key(e.get("original_vocalized", ""), e.get("original_stress", ""))
#         skey = _canonical_key(e.get("suggested_vocalized", ""), e.get("suggested_stress", ""))
#         pair_id = (str(okey), str(skey)) if okey and skey else None

#         if level:
#             level_shown[level] += 1
#         if pair_id:
#             pair_shown[pair_id] += 1
#             pair_display.setdefault(pair_id, (e.get("original_vocalized", ""), e.get("suggested_vocalized", ""), level))

#         if reason == "approved":
#             if level:
#                 level_approved[level] += 1
#             if pair_id:
#                 pair_approved[pair_id] += 1
#             continue

#         # "לא מתאים להקשר" - פוסל רק את ההצעה הבודדת (מטופל ב-feedback_service
#         # דרך get_hard_rejected_words). לא נוגע לאיכות החרוז -> לא נלמד גלובלית.
#         if reason == "bad_context":
#             if suggested:
#                 context_rejected[suggested] += 1
#             continue

#         # "אחר" שלא זוהה כקשור לחרוז (harsh) - פסילה חמורה, לא נלמד כלל.
#         if severity == "harsh":
#             continue

#         # רק "soft" (dislike, או "אחר" שכן קשור לחרוז) תורם ללמידה גלובלית.
#         if severity == "soft":
#             if level:
#                 level_rejected[level] += 1
#                 level_words[level].add(original)
#             if pair_id:
#                 pair_rejected[pair_id] += 1
#                 pair_words[pair_id].add(original)

#         if reason == "other" and e.get("custom", "").strip():
#             custom_texts.append(e["custom"].strip())

#     # --- רמות חרוז בעייתיות (מאוזן מול אישורים + הגנת גיוון) ---
#     bad_levels = []
#     for level, rejected in level_rejected.items():
#         approved = level_approved.get(level, 0)
#         shown = level_shown.get(level, 0)
#         distinct = len(level_words.get(level, set()))
#         net = rejected - approved
#         if (
#             rejected >= MIN_REJECTIONS
#             and distinct >= MIN_DISTINCT_WORDS
#             and shown > 0
#             and net / shown >= MIN_NET_REJECTION_RATE
#         ):
#             bad_levels.append(level)

#     # --- זוגות בעייתיים - נשמרים כ"אותיות+ניקוד+רמה", לא כפונמה מופשטת ---
#     bad_pairs = []
#     for pair_id, rejected in pair_rejected.items():
#         approved = pair_approved.get(pair_id, 0)
#         shown = pair_shown.get(pair_id, 0)
#         distinct = len(pair_words.get(pair_id, set()))
#         net = rejected - approved
#         if (
#             rejected >= MIN_REJECTIONS
#             and distinct >= MIN_DISTINCT_WORDS
#             and shown > 0
#             and net / shown >= MIN_NET_REJECTION_RATE
#         ):
#             orig_voc, sug_voc, lvl = pair_display.get(pair_id, ("", "", 0))
#             bad_pairs.append({
#                 "target_letters_niqud": orig_voc,
#                 "suggested_letters_niqud": sug_voc,
#                 "rhyme_level": lvl,
#             })

#     context_words = [w for w, cnt in context_rejected.items() if cnt >= MIN_REJECTIONS]

#     word_freq: Counter = Counter()
#     for text in custom_texts:
#         for word in text.split():
#             if len(word) >= 3:
#                 word_freq[word] += 1
#     frequent_custom_words = [w for w, cnt in word_freq.most_common(10) if cnt >= 2]

#     total = len(entries)
#     approvals = sum(1 for e in entries if e.get("reason") == "approved")

#     rules = {
#         "bad_rhyme_levels": bad_levels,
#         "bad_key_pairs": bad_pairs,
#         "context_rejected_words": context_words,
#         "frequent_custom_keywords": frequent_custom_words,
#         "total_feedback": total,
#         "approval_rate": round(approvals / total, 2) if total else 0.0,
#     }

#     with open(LEARNED_PATH, "w", encoding="utf-8") as f:
#         json.dump(rules, f, ensure_ascii=False, indent=2)

#     return rules


# def load_rules() -> dict:
#     """טוען את הכללים הנלמדים מהקובץ."""
#     if not os.path.exists(LEARNED_PATH):
#         return {}
#     with open(LEARNED_PATH, encoding="utf-8") as f:
#         return json.load(f)


# def get_min_acceptable_level() -> int:
#     """
#     מחזיר את רמת החרוז המינימלית שהמשתמש מקבל.
#     אם רמה 2 נדחית -> דרוש רמה 1 בלבד.
#     אם רמה 3 נדחית -> דרוש לפחות רמה 2.
#     ברירת מחדל: רמה 3 (מקובל).
#     """
#     rules = load_rules()
#     bad = set(rules.get("bad_rhyme_levels", []))
#     for level in [2, 3, 4]:
#         if level in bad:
#             return level - 1
#     return 3


# def is_bad_pair(original_vocalized: str, original_stress: str,
#                  suggested_vocalized: str, suggested_stress: str) -> bool:
#     """
#     מחזיר True אם זוג המילים המנוקדות הזה נדחה מספיק פעמים כדי להיחשב
#     כלל גלובלי. ההשוואה מתבצעת על בסיס אותיות+ניקוד (כמו שנשמר), ולא על
#     ייצוג פונמה, כדי להימנע מבאגים של ייצוג כפול.
#     """
#     rules = load_rules()
#     for pair in rules.get("bad_key_pairs", []):
#         if (
#             pair.get("target_letters_niqud") == original_vocalized
#             and pair.get("suggested_letters_niqud") == suggested_vocalized
#         ):
#             return True
#     return False
"""
שירות למידה מתגמול (RLHF-lite) עם הגנות מפני הטיה/מניפולציה של משתמש בודד.

עקרונות מרכזיים (בעקבות עדכון הלוגיקה):

1. רק משוב שסווג כ"soft" (services.feedback_service) תורם ללמידה גלובלית
   (רמות/זוגות חרוז בעייתיים). משוב "hard" (לא מתאים להקשר) ו-"harsh"
   ("אחר" שלא זוהה כקשור לחרוז) פוסלים רק את ההצעה הבודדת - הם *לעולם*
   לא מוכללים לכלל שפוסל רמת/זוג חרוז שלמים, כי הם לא נוגעים לאיכות
   החרוז עצמה.

2. "אישרתי" (approved) הוא איתות חיובי שמקוזז מול דחיות: רמה/זוג עם הרבה
   אישורים לא ייפסלו בקלות בגלל מיעוט "לא אהבתי" מקריים.

3. הגנה מפני מניפולציה של משתמש בודד: כלל גלובלי (רמה בעייתית / זוג
   בעייתי) נלמד רק אם:
     - יש לפחות MIN_REJECTIONS דחיות מוחלטות, וגם
     - הן מגיעות מלפחות MIN_DISTINCT_WORDS מילים מקוריות *שונות*
       (כדי שספאם של אותה מילה לא "יפיל" רמת חרוז שלמה), וגם
     - שיעור הדחייה נטו (דחיות פחות אישורים, יחסית להצגות) עובר סף גבוה.

4. הנתונים הנשמרים לכל זוג הם מפתחות החרוז (target_key/suggested_key)
   כפי שחושבו פעם אחת ע"י RhymeChecker ב-pipeline.py והועברו דרך app.py,
   יחד עם רמת החרוז ומילות המקור/ההצעה בפועל - כדי לשמור על ייצוג עקבי
   אחד לכל זוג (זה גם התיקון לבאג הישן שבו אותו זוג חרוז נשמר בשני
   פורמטים שונים בקובץ הכללים, כי מקורות קריאה שונים בקוד המרו אותו
   tuple למחרוזת בפורמט שונה).
"""
import json
import os
from collections import Counter, defaultdict

from services.feedback_service import load_all_feedback

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEARNED_PATH = os.path.join(_BASE, "learned_rules.json")

# --- ספי הגנה מפני מניפולציה ---
MIN_REJECTIONS = 3           # מספר דחיות מוחלט מינימלי לפני שנלמד כלל
MIN_DISTINCT_WORDS = 2       # מס' מילים מקוריות *שונות* שתרמו לדחייה (הגנת גיוון)
MIN_NET_REJECTION_RATE = 0.6 # (דחיות-אישורים)/הצגות מינימלי כדי לפסול רמה/זוג


def analyze_and_save() -> dict:
    """
    קורא את כל המשובים, מנתח דפוסים תוך הגנה מפני מניפולציה, ושומר כללים
    ל-learned_rules.json. מחזיר את הכללים שנלמדו.
    """
    entries = load_all_feedback()
    if not entries:
        return {}

    level_shown, level_rejected, level_approved = Counter(), Counter(), Counter()
    pair_shown, pair_rejected, pair_approved = Counter(), Counter(), Counter()
    level_words: dict[int, set] = defaultdict(set)
    pair_words: dict[tuple, set] = defaultdict(set)
    pair_display: dict[tuple, tuple] = {}

    context_rejected: Counter = Counter()
    custom_texts: list[str] = []

    for e in entries:
        reason = e.get("reason", "")
        severity = e.get("severity") or ""
        level = e.get("rhyme_level", 0)
        original = e.get("original", "")
        suggested = e.get("suggested", "")

        # target_key/suggested_key מגיעים כבר כמחרוזת עקבית מ-save_feedback
        # (str(target_key)/str(suggested_key) שחושבו פעם אחת ע"י RhymeChecker
        # ב-pipeline.py) - לכן משתמשים בהם ישירות כמזהה זוג, במקום לשחזר
        # אותם מחדש ממידע שלא בהכרח קיים.
        tkey = e.get("target_key", "")
        skey = e.get("suggested_key", "")
        pair_id = (tkey, skey) if tkey and skey else None

        if level:
            level_shown[level] += 1
        if pair_id:
            pair_shown[pair_id] += 1
            pair_display.setdefault(pair_id, (original, suggested, level))

        if reason == "approved":
            if level:
                level_approved[level] += 1
            if pair_id:
                pair_approved[pair_id] += 1
            continue

        # "לא מתאים להקשר" - פוסל רק את ההצעה הבודדת (מטופל ב-feedback_service
        # דרך get_hard_rejected_words). לא נוגע לאיכות החרוז -> לא נלמד גלובלית.
        if reason == "bad_context":
            if suggested:
                context_rejected[suggested] += 1
            continue

        # "אחר" שלא זוהה כקשור לחרוז (harsh) - פסילה חמורה, לא נלמד כלל.
        if severity == "harsh":
            continue

        # רק "soft" (dislike, או "אחר" שכן קשור לחרוז) תורם ללמידה גלובלית.
        if severity == "soft":
            if level:
                level_rejected[level] += 1
                level_words[level].add(original)
            if pair_id:
                pair_rejected[pair_id] += 1
                pair_words[pair_id].add(original)

        if reason == "other" and e.get("custom", "").strip():
            custom_texts.append(e["custom"].strip())

    # --- רמות חרוז בעייתיות (מאוזן מול אישורים + הגנת גיוון) ---
    bad_levels = []
    for level, rejected in level_rejected.items():
        approved = level_approved.get(level, 0)
        shown = level_shown.get(level, 0)
        distinct = len(level_words.get(level, set()))
        net = rejected - approved
        if (
            rejected >= MIN_REJECTIONS
            and distinct >= MIN_DISTINCT_WORDS
            and shown > 0
            and net / shown >= MIN_NET_REJECTION_RATE
        ):
            bad_levels.append(level)

    # --- זוגות בעייתיים - נשמרים לפי מפתח RhymeChecker (אותיות+ניקוד מקודדים) ---
    bad_pairs = []
    for pair_id, rejected in pair_rejected.items():
        approved = pair_approved.get(pair_id, 0)
        shown = pair_shown.get(pair_id, 0)
        distinct = len(pair_words.get(pair_id, set()))
        net = rejected - approved
        if (
            rejected >= MIN_REJECTIONS
            and distinct >= MIN_DISTINCT_WORDS
            and shown > 0
            and net / shown >= MIN_NET_REJECTION_RATE
        ):
            orig_word, sug_word, lvl = pair_display.get(pair_id, ("", "", 0))
            bad_pairs.append({
                "target_key": pair_id[0],
                "suggested_key": pair_id[1],
                "target_word": orig_word,
                "suggested_word": sug_word,
                "rhyme_level": lvl,
            })

    context_words = [w for w, cnt in context_rejected.items() if cnt >= MIN_REJECTIONS]

    word_freq: Counter = Counter()
    for text in custom_texts:
        for word in text.split():
            if len(word) >= 3:
                word_freq[word] += 1
    frequent_custom_words = [w for w, cnt in word_freq.most_common(10) if cnt >= 2]

    total = len(entries)
    approvals = sum(1 for e in entries if e.get("reason") == "approved")

    rules = {
        "bad_rhyme_levels": bad_levels,
        "bad_key_pairs": bad_pairs,
        "context_rejected_words": context_words,
        "frequent_custom_keywords": frequent_custom_words,
        "total_feedback": total,
        "approval_rate": round(approvals / total, 2) if total else 0.0,
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
    אם רמה 2 נדחית -> דרוש רמה 1 בלבד.
    אם רמה 3 נדחית -> דרוש לפחות רמה 2.
    ברירת מחדל: רמה 3 (מקובל).
    """
    rules = load_rules()
    bad = set(rules.get("bad_rhyme_levels", []))
    for level in [2, 3, 4]:
        if level in bad:
            return level - 1
    return 3


def is_bad_pair(target_key: str, suggested_key: str) -> bool:
    """
    מחזיר True אם זוג מפתחות החרוז הזה (כפי שחושבו ע"י RhymeChecker
    ונשלחו מ-pipeline.py/app.py) נדחה מספיק פעמים כדי להיחשב כלל גלובלי.
    """
    rules = load_rules()
    for pair in rules.get("bad_key_pairs", []):
        if pair.get("target_key") == target_key and pair.get("suggested_key") == suggested_key:
            return True
    return False