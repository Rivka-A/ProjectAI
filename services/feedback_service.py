# """
# שמירה וטעינה של משובי משתמש.
# כל משוב נשמר כשורת JSON ב-feedback_log.jsonl.

# עיקרון מפתח: המשתמש יכול להזין פידבק כרצונו, אבל לא כל פידבק "שווה" באותה
# מידה מבחינת הלמידה. לכן כל רשומה מסווגת לפי "חומרה" (severity), וה-Pipeline
# ולשירות הלמידה (learning_service) מתייחסים אליה בהתאם:

#     positive  - "אישרתי"           -> מחזק את הדפוס, לא פוסל כלום.
#     soft      - "לא אהבתי" /       -> פוסל את ההצעה הזו כברירת מחדל, אבל אם
#                 "אחר" שקשור לחרוז     אין הצעות אחרות - מותר להחזיר אותה
#                                        בחזרה עם הודעת "לא נמצאו התאמות אחרות".
#                                        תורם ללמידה גלובלית (בזהירות, ראו
#                                        learning_service).
#     hard      - "לא מתאים להקשר"   -> פוסל את ההצעה הספציפית הזו סופית
#                                        (לא יוצג שוב לאותה מילה, גם לא כ-
#                                        Fallback). לא נוגע לאיכות החרוז עצמו,
#                                        ולכן *לא* משפיע על למידה גלובלית.
#     harsh     - "אחר" שלא זוהה     -> פסילה חמורה יותר מ-soft: ההצעה נפסלת
#                 כקשור לחרוז            סופית ולא תוצג אפילו כ-Fallback, בדיוק
#                                        כמו hard, כי אין לנו דרך לדעת אם
#                                        המשוב אמין. גם לא נכנס ללמידה.

# כך משוב חופשי של המשתמש יכול לתרום ללמידה, אבל לא "לשבור" את המערכת -
# כל הצעה ספציפית שנפסלת בגלל הקשר/טקסט לא-רלוונטי נעצרת ברמת ההצעה הבודדת,
# ולא מוכללת לכלל שפוסל רמות/זוגות חרוז שלמים.
# """
# import json
# import os
# from datetime import datetime

# from core.rhyme_checker import RhymeChecker

# _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# LOG_PATH = os.path.join(_BASE, "feedback_log.jsonl")

# REASON_LABELS = {
#     "approved":    "השינוי מבורך ✅",
#     "worse_rhyme": "החרוז פחות טוב ❌",
#     "bad_context": "לא מתאים להקשר 🎭",
#     "dislike":     "לא אהבתי 👎",
#     "other":       "אחר ✏️",
# }

# # --- מיפוי סיבה -> חומרה (severity) ---
# # הערה: "worse_rhyme" נשמר לתאימות לאחור ומטופל כמו "dislike" (soft).
# REASON_SEVERITY = {
#     "approved":    "positive",
#     "dislike":     "soft",
#     "worse_rhyme": "soft",
#     "bad_context": "hard",
#     # "other" נקבע דינמית לפי תוכן הטקסט - ראו resolve_severity()
# }

# # סיבות שתורמות (בזהירות) ללמידה גלובלית על איכות חרוז
# RHYME_QUALITY_SEVERITIES = {"soft"}

# # מילות מפתח לזיהוי אם טקסט חופשי ("אחר") אכן נוגע לאיכות/צליל החרוז עצמו,
# # ולא לעניין אחר (הקשר, תוכן, טעם אישי לא-פונטי וכו').
# _RHYME_RELATED_KEYWORDS = [
#     "חרוז", "מתחרז", "חריזה", "תנועה", "עיצור", "הברה", "סיומת", "סיום",
#     "נשמע", "צליל", "פונטי", "משקל", "קצב", "אסונאנס", "מלרע", "מלעיל",
#     "דומה", "לא דומה", "אותו צליל",
# ]


# def is_custom_text_rhyme_related(text: str) -> bool:
#     """היוריסטיקה: האם טקסט "אחר" חופשי שהמשתמש הזין נוגע לאיכות החרוז עצמו.
#     אם לא - הפידבק לא ישמש ללמידה גלובלית ויטופל בחומרה הגבוהה ביותר,
#     כי אין דרך לאמת שהוא אמין/רלוונטי לחרוז."""
#     if not text:
#         return False
#     t = text.strip()
#     return any(kw in t for kw in _RHYME_RELATED_KEYWORDS)


# def resolve_severity(reason: str, custom_text: str = "") -> str:
#     """קובע את חומרת המשוב בפועל. מטפל במיוחד ב"אחר", שחומרתו תלוית-תוכן."""
#     if reason == "other":
#         return "soft" if is_custom_text_rhyme_related(custom_text) else "harsh"
#     return REASON_SEVERITY.get(reason, "soft")


# def save_feedback(
#     original_word: str,
#     suggested_word: str,
#     reason: str,
#     custom_text: str = "",
#     original_vocalized: str = "",
#     original_stress: str = "",
#     suggested_vocalized: str = "",
#     suggested_stress: str = "",
# ) -> dict:
#     """
#     שומר רשומת משוב אחת ומחזיר אותה (כדי שהקורא יוכל להציג הודעה מתאימה).

#     רמת החרוז (rhyme_level) *תמיד* נגזרת מ-RhymeChecker על סמך הניקוד בפועל,
#     ולא מוזנת ידנית ע"י המשתמש - כדי שהלמידה תתבסס על מקור אמת פונטי אחד,
#     ולא תהיה פתוחה למניפולציה חופשית.

#     המפתח הנשמר הוא "אותיות + ניקוד" (המילה המנוקדת עצמה), לא ייצוג פונמה
#     מופשט - כך שהנתונים קריאים, ניתנים לביקורת, ואינם תלויים במימוש הפנימי
#     של RhymeChecker (זה גם מתקן את הבאג הישן שבו אותו זוג חרוז נשמר בשני
#     ייצוגים שונים בקובץ הכללים).
#     """
#     rhyme_level = 5
#     try:
#         if original_vocalized and suggested_vocalized:
#             k1 = RhymeChecker.extract_rhyme_key(original_vocalized, original_stress or "מלרע")
#             k2 = RhymeChecker.extract_rhyme_key(suggested_vocalized, suggested_stress or "מלרע")
#             rhyme_level = RhymeChecker.rhyme_level(k1, k2)
#     except Exception:
#         pass

#     severity = resolve_severity(reason, custom_text)
#     rhyme_related_other = (reason == "other" and severity == "soft")

#     entry = {
#         "ts": datetime.utcnow().isoformat(),
#         "original": original_word,
#         "suggested": suggested_word,
#         "reason": reason,
#         "custom": custom_text,
#         "original_vocalized": original_vocalized,
#         "original_stress": original_stress,
#         "suggested_vocalized": suggested_vocalized,
#         "suggested_stress": suggested_stress,
#         "rhyme_level": rhyme_level,
#         "severity": severity,
#         "rhyme_related_other": rhyme_related_other,
#     }
#     with open(LOG_PATH, "a", encoding="utf-8") as f:
#         f.write(json.dumps(entry, ensure_ascii=False) + "\n")

#     return entry


# def feedback_response_message(entry: dict) -> str:
#     """הודעה חוזרת מתאימה למשתמש בהתאם לסוג/חומרת המשוב שהוזן."""
#     reason = entry.get("reason")
#     severity = entry.get("severity")
#     if reason == "approved":
#         return "תודה! השינוי אושר והמערכת תעדיף דפוסים דומים בעתיד."
#     if severity == "hard":
#         return "הובן - ההצעה נפסלה בגלל אי-התאמה להקשר ולא תוצע שוב למילה זו."
#     if severity == "harsh":
#         return "הובן - מכיוון שההערה אינה נוגעת לאיכות החרוז, ההצעה נפסלה סופית ולא תילמד כלל שיטתי."
#     if severity == "soft":
#         return "תודה על המשוב - ההצעה תוחלף בברירת מחדל, ותוצג שוב רק אם לא יימצאו התאמות אחרות."
#     return "תודה על המשוב."


# def load_all_feedback() -> list[dict]:
#     if not os.path.exists(LOG_PATH):
#         return []
#     entries = []
#     with open(LOG_PATH, encoding="utf-8") as f:
#         for line in f:
#             try:
#                 entries.append(json.loads(line))
#             except json.JSONDecodeError:
#                 print(f"Warning: could not parse line in feedback log: {line.strip()} feedback_service 57")
#                 continue
#     return entries


# def get_rejection_info(original_word: str) -> dict[str, str]:
#     """
#     מחזיר מיפוי {מילה_מוצעת: חומרה} עבור כל המילים שנדחו בעבר עבור original_word.
#     'hard' / 'harsh' -> פסילה סופית, גם כ-Fallback.
#     'soft'           -> חסימה כברירת מחדל, אך מותר כ-Fallback עם אזהרה.
#     אם אותה מילה הוזנה בכמה חומרות שונות (למשל גם "לא אהבתי" וגם "לא מתאים
#     להקשר"), נשמרת החומרה החמורה ביותר שנרשמה אי-פעם - לא ניתן "לרכך" פסילה
#     חמורה ע"י אישור/דחייה קלה מאוחרת יותר.
#     """
#     severity_rank = {"soft": 1, "hard": 2, "harsh": 2}
#     info: dict[str, str] = {}
#     for entry in load_all_feedback():
#         if entry.get("original") != original_word:
#             continue
#         reason = entry.get("reason")
#         if reason == "approved":
#             continue
#         word = entry.get("suggested")
#         if not word:
#             continue
#         severity = entry.get("severity") or resolve_severity(reason, entry.get("custom", ""))
#         if severity not in severity_rank:
#             continue
#         current = info.get(word)
#         if current is None or severity_rank[severity] > severity_rank.get(current, 0):
#             info[word] = severity
#     return info


# def get_rejected_words(original_word: str) -> set[str]:
#     """נשמר לתאימות לאחור: כל המילים שנדחו (בכל חומרה)."""
#     return set(get_rejection_info(original_word).keys())


# def get_hard_rejected_words(original_word: str) -> set[str]:
#     """מילים שנפסלו סופית - לא יוצגו אפילו כ-Fallback."""
#     return {w for w, sev in get_rejection_info(original_word).items() if sev in ("hard", "harsh")}


# def get_soft_rejected_words(original_word: str) -> set[str]:
#     """מילים שנחסמות כברירת מחדל, אך מותרות כ-Fallback עם הודעת אזהרה."""
#     return {w for w, sev in get_rejection_info(original_word).items() if sev == "soft"}

"""
שמירה וטעינה של משובי משתמש.
כל משוב נשמר כשורת JSON ב-feedback_log.jsonl.

עיקרון מפתח: המשתמש יכול להזין פידבק כרצונו, אבל לא כל פידבק "שווה" באותה
מידה מבחינת הלמידה. לכן כל רשומה מסווגת לפי "חומרה" (severity), וה-Pipeline
ולשירות הלמידה (learning_service) מתייחסים אליה בהתאם:

    positive  - "אישרתי"           -> מחזק את הדפוס, לא פוסל כלום.
    soft      - "לא אהבתי" /       -> פוסל את ההצעה הזו כברירת מחדל, אבל אם
                "אחר" שקשור לחרוז     אין הצעות אחרות - מותר להחזיר אותה
                                       בחזרה עם הודעת "לא נמצאו התאמות אחרות".
                                       תורם ללמידה גלובלית (בזהירות, ראו
                                       learning_service).
    hard      - "לא מתאים להקשר"   -> פוסל את ההצעה הספציפית הזו סופית
                                       (לא יוצג שוב לאותה מילה, גם לא כ-
                                       Fallback). לא נוגע לאיכות החרוז עצמו,
                                       ולכן *לא* משפיע על למידה גלובלית.
    harsh     - "אחר" שלא זוהה     -> פסילה חמורה יותר מ-soft: ההצעה נפסלת
                כקשור לחרוז            סופית ולא תוצג אפילו כ-Fallback, בדיוק
                                       כמו hard, כי אין לנו דרך לדעת אם
                                       המשוב אמין. גם לא נכנס ללמידה.

כך משוב חופשי של המשתמש יכול לתרום ללמידה, אבל לא "לשבור" את המערכת -
כל הצעה ספציפית שנפסלת בגלל הקשר/טקסט לא-רלוונטי נעצרת ברמת ההצעה הבודדת,
ולא מוכללת לכלל שפוסל רמות/זוגות חרוז שלמים.
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

# --- מיפוי סיבה -> חומרה (severity) ---
# הערה: "worse_rhyme" נשמר לתאימות לאחור ומטופל כמו "dislike" (soft).
REASON_SEVERITY = {
    "approved":    "positive",
    "dislike":     "soft",
    "worse_rhyme": "soft",
    "bad_context": "hard",
    # "other" נקבע דינמית לפי תוכן הטקסט - ראו resolve_severity()
}

# סיבות שתורמות (בזהירות) ללמידה גלובלית על איכות חרוז
RHYME_QUALITY_SEVERITIES = {"soft"}

# מילות מפתח לזיהוי אם טקסט חופשי ("אחר") אכן נוגע לאיכות/צליל החרוז עצמו,
# ולא לעניין אחר (הקשר, תוכן, טעם אישי לא-פונטי וכו').
_RHYME_RELATED_KEYWORDS = [
    "חרוז", "מתחרז", "חריזה", "תנועה", "עיצור", "הברה", "סיומת", "סיום",
    "נשמע", "צליל", "פונטי", "משקל", "קצב", "אסונאנס", "מלרע", "מלעיל",
    "דומה", "לא דומה", "אותו צליל",
]


def is_custom_text_rhyme_related(text: str) -> bool:
    """היוריסטיקה: האם טקסט "אחר" חופשי שהמשתמש הזין נוגע לאיכות החרוז עצמו.
    אם לא - הפידבק לא ישמש ללמידה גלובלית ויטופל בחומרה הגבוהה ביותר,
    כי אין דרך לאמת שהוא אמין/רלוונטי לחרוז."""
    if not text:
        return False
    t = text.strip()
    return any(kw in t for kw in _RHYME_RELATED_KEYWORDS)


def resolve_severity(reason: str, custom_text: str = "") -> str:
    """קובע את חומרת המשוב בפועל. מטפל במיוחד ב"אחר", שחומרתו תלוית-תוכן."""
    if reason == "other":
        return "soft" if is_custom_text_rhyme_related(custom_text) else "harsh"
    return REASON_SEVERITY.get(reason, "soft")


def save_feedback(
    original_word: str,
    suggested_word: str,
    reason: str,
    custom_text: str = "",
    target_key: str = "",
    suggested_key: str = "",
    rhyme_level: int = 0,
) -> dict:
    """
    שומר רשומת משוב אחת ומחזיר אותה (כדי שהקורא יוכל להציג הודעה מתאימה).

    rhyme_level מגיע כאן כבר מחושב ע"י RhymeChecker (ב-pipeline.py, כחלק מ-
    replacements_info) - הוא *לא* מוזן ידנית ע"י המשתמש, אלא רק מועבר הלאה
    ע"י שכבת ה-UI (app.py). כך שהמקור האמיתי לרמת החרוז נשאר תמיד
    RhymeChecker, בהתאם לדרישה שהלמידה תתבסס על מקור אמת פונטי אחד ולא
    תהיה פתוחה למניפולציה חופשית של המשתמש.

    target_key / suggested_key הם ייצוג המחרוזת של מפתח החרוז (כפי
    שחושב ע"י RhymeChecker.extract_rhyme_key) - הם מקודדים בתוכם את
    האותיות והניקוד הרלוונטיים לחריזה, ונשמרים כפי שהתקבלו כדי שאותו
    זוג חרוז תמיד ישמור על אותו ייצוג עקבי (זה גם התיקון לבאג הישן שבו
    אותו זוג חרוז נשמר בשני פורמטים שונים בקובץ הכללים).
    """
    severity = resolve_severity(reason, custom_text)
    rhyme_related_other = (reason == "other" and severity == "soft")

    entry = {
        "ts": datetime.utcnow().isoformat(),
        "original": original_word,
        "suggested": suggested_word,
        "reason": reason,
        "custom": custom_text,
        "target_key": target_key,
        "suggested_key": suggested_key,
        "rhyme_level": rhyme_level,
        "severity": severity,
        "rhyme_related_other": rhyme_related_other,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def feedback_response_message(entry: dict) -> str:
    """הודעה חוזרת מתאימה למשתמש בהתאם לסוג/חומרת המשוב שהוזן."""
    reason = entry.get("reason")
    severity = entry.get("severity")
    if reason == "approved":
        return "תודה! השינוי אושר והמערכת תעדיף דפוסים דומים בעתיד."
    if severity == "hard":
        return "הובן - ההצעה נפסלה בגלל אי-התאמה להקשר ולא תוצע שוב למילה זו."
    if severity == "harsh":
        return "הובן - מכיוון שההערה אינה נוגעת לאיכות החרוז, ההצעה נפסלה סופית ולא תילמד כלל שיטתי."
    if severity == "soft":
        return "תודה על המשוב - ההצעה תוחלף בברירת מחדל, ותוצג שוב רק אם לא יימצאו התאמות אחרות."
    return "תודה על המשוב."


def load_all_feedback() -> list[dict]:
    if not os.path.exists(LOG_PATH):
        return []
    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Warning: could not parse line in feedback log: {line.strip()} feedback_service 57")
                continue
    return entries


def get_rejection_info(original_word: str) -> dict[str, str]:
    """
    מחזיר מיפוי {מילה_מוצעת: חומרה} עבור כל המילים שנדחו בעבר עבור original_word.
    'hard' / 'harsh' -> פסילה סופית, גם כ-Fallback.
    'soft'           -> חסימה כברירת מחדל, אך מותר כ-Fallback עם אזהרה.
    אם אותה מילה הוזנה בכמה חומרות שונות (למשל גם "לא אהבתי" וגם "לא מתאים
    להקשר"), נשמרת החומרה החמורה ביותר שנרשמה אי-פעם - לא ניתן "לרכך" פסילה
    חמורה ע"י אישור/דחייה קלה מאוחרת יותר.
    """
    severity_rank = {"soft": 1, "hard": 2, "harsh": 2}
    info: dict[str, str] = {}
    for entry in load_all_feedback():
        if entry.get("original") != original_word:
            continue
        reason = entry.get("reason")
        if reason == "approved":
            continue
        word = entry.get("suggested")
        if not word:
            continue
        severity = entry.get("severity") or resolve_severity(reason, entry.get("custom", ""))
        if severity not in severity_rank:
            continue
        current = info.get(word)
        if current is None or severity_rank[severity] > severity_rank.get(current, 0):
            info[word] = severity
    return info


def get_rejected_words(original_word: str) -> set[str]:
    """נשמר לתאימות לאחור: כל המילים שנדחו (בכל חומרה)."""
    return set(get_rejection_info(original_word).keys())


def get_hard_rejected_words(original_word: str) -> set[str]:
    """מילים שנפסלו סופית - לא יוצגו אפילו כ-Fallback."""
    return {w for w, sev in get_rejection_info(original_word).items() if sev in ("hard", "harsh")}


def get_soft_rejected_words(original_word: str) -> set[str]:
    """מילים שנחסמות כברירת מחדל, אך מותרות כ-Fallback עם הודעת אזהרה."""
    return {w for w, sev in get_rejection_info(original_word).items() if sev == "soft"}