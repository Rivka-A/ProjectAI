# -*- coding: utf-8 -*-
"""
⚠️ טסט-תיעוד לבאג ארכיטקטוני אמיתי ⚠️

בקוד יש שני מנגנוני "רמת חרוז" נפרדים שרצים במקביל:

  * core.rhyme_checker.RhymeChecker.rhyme_level      -> סולם 1-5
  * services.phonetic_rhyme_checker.compare_phonetic_suffixes -> סולם 1-4

pipeline.py (analyze_poem_and_get_suggestions, render_poem_html)
משתמש אך ורק בסולם הפונטי (1-4).
suggestion_service.py / improved_suggestion_service.py / learning_service.py
משתמשים אך ורק בסולם של RhymeChecker (1-5).

הבעיה: שני ה"level" נכתבים לאותו קובץ feedback_log.jsonl תחת אותו
שם שדה ("rhyme_level"), ו-learning_service מנתח אותם יחד כאילו הם
אותו דבר (get_min_acceptable_level / is_bad_pair). בפועל level=2
פירושו "חרוז טוב לגמרי" בסולם הפונטי, אבל "חרוז סביר-בינוני" בסולם
של RhymeChecker. תוצאה אפשרית: אם המשתמש דוחה הרבה הצעות ברמה 2
שמקורן ב-suggestion_service (RhymeChecker), הכלל הנלמד ("דרוש רמה 1
בלבד") ייאכף גם על pipeline.py (סולם פונטי) - איפה ש"רמה 1" ו"רמה 2"
שניהם כבר נחשבים חרוז מצוין. זה עלול לגרום לסינון-יתר אגרסיבי
במקום שגוי.

הטסט הבא לא "נכשל" בכוונה - הוא ממחיש את חוסר ההתאמה בעזרת דוגמה
קונקרטית, כדי שכל שינוי עתידי (איחוד הסולמות, או הפרדת המפתחות
הנלמדים לפי מקור) יצטרך לעדכן את הציפייה כאן במפורש.
"""
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.phonetic_rhyme_checker import get_phonetic_suffix, compare_phonetic_suffixes


def _core_level(w1, w2):
    k1 = RhymeChecker.extract_rhyme_key(w1, StressDetector.detect_stress(w1))
    k2 = RhymeChecker.extract_rhyme_key(w2, StressDetector.detect_stress(w2))
    return RhymeChecker.rhyme_level(k1, k2)


def _phonetic_level(w1, w2):
    s1 = get_phonetic_suffix(w1, StressDetector.detect_stress(w1))
    s2 = get_phonetic_suffix(w2, StressDetector.detect_stress(w2))
    return compare_phonetic_suffixes(s1, s2)


def test_the_two_scales_disagree_on_a_textbook_perfect_rhyme():
    """יָד / בָּד הוא חרוז מושלם קלאסי (רק העיצור הפותח שונה)."""
    core = _core_level("יָד", "בָּד")
    phon = _phonetic_level("יָד", "בָּד")

    # התיעוד של המצב הקיים היום:
    assert phon == 1, "בסולם הפונטי זה 'מושלם' (level 1) - כצפוי בעברית"
    assert core == 2, (
        "בסולם של RhymeChecker זה 'רק' level 2, לא level 1 - "
        "כלומר '2' באותו סולם *לא* שקול ל-'2' בסולם השני"
    )


def test_vowel_mismatch_ranked_differently_by_each_system():
    """אָדָם / אָדוֹם: תנועה שונה, עיצור סופי משותף."""
    core = _core_level("אָדָם", "אָדוֹם")
    phon = _phonetic_level("אָדָם", "אָדוֹם")

    assert core == 3, "RhymeChecker נותן קרדיט חלקי לעיצור משותף למרות תנועה שונה"
    assert phon == 4, "הסולם הפונטי מתייחס לכל אי-התאמת תנועה כ'אין חרוז' (הכי גרוע)"
    assert core != phon


def test_recommendation_for_fix():
    """
    לא טסט פונקציונלי - תיעוד המלצה.
    הפתרון המומלץ: להוסיף לכל רשומת feedback שדה 'level_system'
    ('core' / 'phonetic'), ולגרום ל-learning_service.analyze_and_save
    לבנות bad_rhyme_levels / bad_key_pairs *בנפרד* לכל מערכת, ולא
    להתייחס אליהם כאילו הם אותו ציר מספרי.
    """
    assert True
