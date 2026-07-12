# -*- coding: utf-8 -*-
"""
טסטים ל-StressDetector.

הערה חשובה: זהו מזהה הטעמה מבוסס-כללים (heuristic), לא מודל שפה.
ברירת המחדל שלו היא 'מלרע' (רוב המילים בעברית), עם כמה חוקים מפורשים
שתופסים 'מלעיל' (סגוליים, ולייל/הצלחה וכו'). הטסטים כאן נועדו:
  1. לנעול (lock) את ההתנהגות הנוכחית כך שכל שינוי עתידי בקוד
     יידרש לעדכן טסט במפורש (regression safety net).
  2. לתעד מקרי קצה ידועים שבהם החוק לא בהכרח נכון תמיד.
"""
import pytest
from core.stress_detector import StressDetector


class TestDefaultMilra:
    """מילים "רגילות" בלי חוק מיוחד -> ברירת מחדל מלרע."""

    @pytest.mark.parametrize("word", [
        "שָׁלוֹם",
        "אָדָם",
        "גַּן",
        "יָד",
        "אָרוֹן",
    ])
    def test_default_is_milra(self, word):
        assert StressDetector.detect_stress(word) == "מלרע"


class TestSegolatePattern:
    """חוק הסגוליים הכללי: 2+ סגולים -> מלעיל."""

    @pytest.mark.parametrize("word", [
        "חֶלֶד",
        "יֶלֶד",
        "בַּנֶּגֶב",
    ])
    def test_double_segol_is_milra_shifted_to_milel(self, word):
        assert StressDetector.detect_stress(word) == "מלעיל"


class TestQamatsHeException:
    """
    חוק סיומת קמץ-ה: מלעיל רק אם האות שלפני-האחרונה (קודם לתנועה
    הלפני-אחרונה) מכילה שווא, וגם האות הראשונה מכילה פתח (לילה, ביתה).
    הצלחה - למרות שמסתיימת בקמץ-ה - היא מלרע (אין שווא במקום הנדרש).
    """

    def test_layla_is_milel(self):
        assert StressDetector.detect_stress("לַיְלָה") == "מלעיל"

    def test_hatzlacha_is_milra(self):
        # מילה תקנית שמסתיימת קמץ-ה אך ההברה הלפני-אחרונה איננה שווא
        assert StressDetector.detect_stress("הַצְלָחָה") == "מלרע"

    def test_lama_is_milra_by_this_rule(self):
        # תיעוד התנהגות נוכחית: 'לָמָּה' לא עומד בתנאי (אין שווא),
        # ולכן מסווג מלרע לפי הכללים הקיימים - גם אם בפועל ההגייה
        # המקובלת ל'לָמָּה' (why) היא מלעיל. זהו מקרה קצה ידוע שכדאי
        # לתעד ולא "לתקן בהפתעה" בלי לבדוק את ההשלכות במקומות אחרים.
        assert StressDetector.detect_stress("לָמָּה") == "מלרע"


class TestEleException:
    """אֵלֶּה: יש צירה + סגול -> מלעיל (חוק #3)."""

    def test_eleh_is_milel(self):
        assert StressDetector.detect_stress("אֵלֶּה") == "מלעיל"


class TestRobustness:
    """המזהה לא אמור לזרוק חריגה על קלט לא צפוי."""

    @pytest.mark.parametrize("word", ["", "שלום", "abc", "   ", "א"])
    def test_no_crash_on_edge_inputs(self, word):
        result = StressDetector.detect_stress(word)
        assert result in ("מלרע", "מלעיל")

    def test_unvocalized_word_defaults_to_milra(self):
        # מילה בלי ניקוד כלל - אין לה תווי ניקוד שיפעילו אף חוק
        assert StressDetector.detect_stress("שלום") == "מלרע"
