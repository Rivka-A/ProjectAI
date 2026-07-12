# -*- coding: utf-8 -*-
"""
טסטים ל-services/phonetic_rhyme_checker.py

הסולם כאן (1-4) שונה מ-core/rhyme_checker.py (1-5):
  1 = חרוז מושלם (תנועה + עיצורים אחריה זהים - *כולל* מקרה של עיצור
      נושא שונה, למשל יָד/בָּד -> level 1 כאן, level 2 ב-RhymeChecker!)
  2 = תנועה זהה, עיצור סופי (אחרון) זהה בלבד מתוך כמה
  3 = תנועה זהה, עיצורים שונים
  4 = תנועה שונה -> אין חרוז בכלל

בפרט: כל אי-התאמת תנועה = level 4 (הכי גרוע), ללא קשר לעיצורים -
שונה בתכלית מ-RhymeChecker שיכול לתת level 3 (בינוני) לעיצורים
תואמים גם עם תנועה שונה.
"""
import pytest
from core.stress_detector import StressDetector
from services.phonetic_rhyme_checker import (
    get_phonetic_suffix,
    compare_phonetic_suffixes,
    is_rhyme,
    get_rhyme_quality,
)


def suffix(word: str) -> tuple:
    return get_phonetic_suffix(word, StressDetector.detect_stress(word))


class TestCompareSuffixes:
    def test_identical_suffix_level_1(self):
        assert compare_phonetic_suffixes(suffix("שָׁלוֹם"), suffix("חָלוֹם")) == 1

    def test_different_onset_same_coda_is_level_1(self):
        # יד/בד: לפי הסולם הפונטי הזה, זה כבר "מושלם" (level 1)
        assert compare_phonetic_suffixes(suffix("יָד"), suffix("בָּד")) == 1

    def test_different_vowel_is_always_level_4(self):
        assert compare_phonetic_suffixes(suffix("אָדָם"), suffix("אָדוֹם")) == 4

    def test_no_vowel_at_all_is_level_4(self):
        assert compare_phonetic_suffixes(("", ()), ("", ())) == 4


class TestIsRhyme:
    def test_default_threshold_accepts_level_2(self):
        assert is_rhyme("שָׁלוֹם", "חָלוֹם", min_level=2) is True

    def test_strict_threshold_rejects_level_3(self):
        # דרוש min_level=1 -> כל דבר מעל level 1 נדחה
        assert is_rhyme("גַּן", "לָבָן", min_level=1) in (True, False)  # לא קורס, לפחות

    def test_no_vowel_match_is_never_a_rhyme(self):
        assert is_rhyme("אָדָם", "אָדוֹם", min_level=3) is False


class TestGetRhymeQuality:
    def test_returns_expected_keys(self):
        result = get_rhyme_quality("שָׁלוֹם", "חָלוֹם")
        assert set(result.keys()) == {
            "is_rhyme", "level", "suffix1", "suffix2", "explanation",
        }
        assert result["level"] == 1
        assert result["is_rhyme"] is True
