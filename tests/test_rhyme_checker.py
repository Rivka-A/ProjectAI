# -*- coding: utf-8 -*-
"""
טסטים ל-RhymeChecker (core/rhyme_checker.py).

חשוב להבין את הסולם הזה לפני שממשיכים:
  1 = הזנב הפונטי כולה (כולל העיצור הנושא) זהה - כמעט/ממש אותה סיומת מילה.
  2 = ההברה הסופית זהה (תנועה + עיצורים אחריה), אך העיצור הנושא שונה
      -> זה בפועל "חרוז טוב" קלאסי (יָד/בָּד, שָׁלוֹם/חֲלוֹם עם תחילית שונה).
  3 = עיצורים סופיים זהים, תנועה שונה.
  4 = תנועה סופית זהה, עיצורים שונים.
  5 = אין קשר.

זה *שונה* מהסולם ב-phonetic_rhyme_checker.py (1-4, שם "1" כבר נחשב
המצב הטוב ביותר). ראו test_cross_system_consistency.py להרחבה.
"""
import pytest
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector


def key(word: str) -> tuple:
    stress = StressDetector.detect_stress(word)
    return RhymeChecker.extract_rhyme_key(word, stress)


class TestRhymeLevelScale:
    def test_identical_words_level_1(self):
        assert RhymeChecker.rhyme_level(key("שָׁלוֹם"), key("שָׁלוֹם")) == 1

    def test_same_last_syllable_different_onset_level_2(self):
        # יד / בד: אותה הברה סופית (A + ד), עיצור נושא שונה (י מול ב)
        assert RhymeChecker.rhyme_level(key("יָד"), key("בָּד")) == 2

    def test_shalom_vs_chalom_level_1(self):
        # שני עיצורים תואמים ברצף + תנועה -> תא עצמו כתא
        assert RhymeChecker.rhyme_level(key("שָׁלוֹם"), key("חָלוֹם")) == 1

    def test_same_final_consonant_different_vowel_level_3(self):
        # אָדָם (A) מול אָדוֹם (O) - עיצור ם משותף, תנועה שונה
        assert RhymeChecker.rhyme_level(key("אָדָם"), key("אָדוֹם")) == 3

    def test_no_relation_level_5(self):
        assert RhymeChecker.rhyme_level(key("שָׁלוֹם"), key("סֵפֶר")) == 5

    def test_symmetric(self):
        k1, k2 = key("גַּן"), key("לָבָן")
        assert RhymeChecker.rhyme_level(k1, k2) == RhymeChecker.rhyme_level(k2, k1)


class TestExtractRhymeKeyStressSensitivity:
    """המפתח צריך להשתנות בהתאם למיקום ההטעמה (מלרע מול מלעיל)."""

    def test_milra_vs_milel_give_different_tails(self):
        # אותה מילה, שתי הטעמות היפותטיות -> ציפייה לזנבות שונים
        milra_key = RhymeChecker.extract_rhyme_key("לַיְלָה", "מלרע")
        milel_key = RhymeChecker.extract_rhyme_key("לַיְלָה", "מלעיל")
        assert milra_key != milel_key


class TestEmptyAndEdgeInputs:
    def test_empty_word_returns_empty_key(self):
        assert RhymeChecker.extract_rhyme_key("", "מלרע") == ()

    def test_rhyme_level_of_two_empty_keys_is_1(self):
        # key1 == key2 == () -> נכנס ישר ל-"if key1 == key2: return 1"
        assert RhymeChecker.rhyme_level((), ()) == 1


class TestAnalyzeStanza:
    def _meta(self, word):
        return {
            "original_word": word,
            "last_word_vocalized": word,
            "stress_type": StressDetector.detect_stress(word),
        }

    def test_detects_aabb_pattern(self):
        lines = [
            self._meta("שָׁלוֹם"),
            self._meta("חָלוֹם"),
            self._meta("יָד"),
            self._meta("בָּד"),
        ]
        report = RhymeChecker.analyze_stanza(lines)
        assert report["expected_pairs_indices"] == [(0, 1), (2, 3)]
        # שים לב: 'יד'/'בד' הן ברמה 2 (הברה סופית זהה, עיצור נושא שונה),
        # ורק level==1 מדולג מהאלרטים -> גם חרוז "טוב" כמו יד/בד
        # ידווח כאן כאלרט. זו התנהגות נוכחית חשובה לתעד: הפונקציה הזו
        # נדיבה הרבה פחות ממה ש-phonetic_rhyme_checker מגדיר כ"מושלם".
        alert_lines = [a["lines"] for a in report["alerts"]]
        assert (3, 4) in alert_lines

    def test_short_stanza_returns_undefined_pattern(self):
        lines = [self._meta("שָׁלוֹם")]
        report = RhymeChecker.analyze_stanza(lines)
        assert report["pattern"] == "לא מוגדר"
        assert "הבית קצר מדי" in report["alerts"]
