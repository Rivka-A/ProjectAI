# -*- coding: utf-8 -*-
"""
טסטים ל-improved_suggestion_service.py ו-suggestion_service.py אחרי
האיחוד לסולם הפונטי (1-4) במקום RhymeChecker.rhyme_level (1-5).

כל הטסטים כאן משתמשים ב-monkeypatch על get_fill_mask_suggestions כדי
לא להזדקק לרשת/מודלים כבדים (נקדן, HeBERT).
"""
import pytest

from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.phonetic_rhyme_checker import get_phonetic_suffix
import services.improved_suggestion_service as isv
import services.suggestion_service as sv


def full_key(word: str) -> tuple:
    return RhymeChecker.extract_rhyme_key(word, StressDetector.detect_stress(word))


def suffix(word: str) -> tuple:
    return get_phonetic_suffix(word, StressDetector.detect_stress(word))


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """מוודא שאף טסט כאן לא באמת פונה לנקדן/BERT."""
    monkeypatch.setattr(isv, "get_fill_mask_suggestions", lambda *a, **k: [])
    monkeypatch.setattr(isv, "get_contextual_suggestions", lambda *a, **k: [])
    monkeypatch.setattr(sv, "get_fill_mask_suggestions", lambda *a, **k: [])
    monkeypatch.setattr(sv, "get_contextual_suggestions", lambda *a, **k: [])


class TestImprovedSuggestionServiceUsesPhoneticScale:
    def test_levels_returned_are_1_to_3_not_1_to_5(self, monkeypatch):
        monkeypatch.setattr(
            isv, "get_fill_mask_suggestions",
            lambda *a, **k: ["חָלוֹם", "תְּהוֹם", "אָדָם", "מֶלֶךְ"],
        )
        target = full_key("שָׁלוֹם")
        suggestions = isv.get_suggestions_by_rhyme(
            ["x"], 0, "שָׁלוֹם", target, 4, set()
        )
        words = {w for w, _ in suggestions}
        levels = {lvl for _, lvl in suggestions}
        # אדם/מלך לא מתחרזים בכלל עם שלום (תנועה שונה) -> level 4 -> מסוננים
        assert "אָדָם" not in words
        assert "מֶלֶךְ" not in words
        assert levels.issubset({1, 2, 3})
        assert "חָלוֹם" in words and "תְּהוֹם" in words

    def test_improve_poem_rhyme_matches_pipeline_threshold(self, monkeypatch):
        # שורות 1-2 מתחרזות (שלום/חלום), 3-4 לא (אדם/מלך)
        lines = ["א שָׁלוֹם", "ב חָלוֹם", "ג אָדָם", "ד מֶלֶךְ"]
        report = isv.improve_poem_rhyme(lines)
        problem_pairs = {tuple(sorted(i["lines"])) for i in report["issues"]}
        # (1,2) לא אמור להיות בעיה כי level<=2 (חרוז טוב)
        assert (1, 2) not in problem_pairs
        # (3,4) כן אמור להיות בעיה
        assert (3, 4) in problem_pairs


class TestSuggestionServiceEffectiveMaxLevelActuallyFilters:
    """
    לפני התיקון: effective_max_level חושב אבל מעולם לא סינן בפועל,
    ו-combined תמיד כלל את כל הרמות 1-4. הטסט הזה נועל שהתיקון עובד.
    """

    def test_only_levels_up_to_effective_max_are_included_without_fallback(self, monkeypatch):
        # 5 מילים אמיתיות ברמה 1 (מתחרזות מצוין עם שָׁלוֹם) + 2 הסחות דעת
        # ברמה 4 (לא מתחרזות בכלל) - כדי לוודא ש-combined>=5 בלי fallback,
        # ושהמילים ברמה 4 לא נכנסות למרות שהיו ב-raw.
        level1_words = ["חָלוֹם", "תְּהוֹם", "מָקוֹם", "סְדוֹם", "חֲלוֹם"]
        level4_words = ["אָדָם", "מֶלֶךְ"]
        monkeypatch.setattr(
            sv, "get_fill_mask_suggestions",
            lambda *a, **k: level1_words + level4_words,
        )
        target = suffix("שָׁלוֹם")
        # orig_level=1 -> effective_max_level = min(1, learned_min_level(=3 default)) = 1
        result = sv.build_candidates(["x"], 0, "שָׁלוֹם", target, 1, set())
        assert len(result) >= 5, "combined should already have >=5 from level-1 bucket alone"
        for w in level4_words:
            assert w not in result, (
                f"'{w}' is level 4 (no rhyme at all) but leaked in even though "
                "the level-1 bucket already had enough candidates"
            )


class TestBadPairUsesConsistentKeySpace:
    """
    is_bad_pair צריך עכשיו לקבל ולהשוות מפתחות בפורמט סיומת פונטית
    (str של tuple (vowel, consonants)), בדיוק כמו מה ש-pipeline.py
    שומר בפועל ב-replacements_info, ולא string-ים של מפתחות RhymeChecker
    גולמיים כמו קודם.
    """

    def test_learned_bad_pair_is_excluded_including_from_fallback(self, monkeypatch, isolated_feedback):
        feedback_service, learning_service = isolated_feedback
        monkeypatch.setattr(
            sv, "get_fill_mask_suggestions",
            lambda *a, **k: ["חָלוֹם", "תְּהוֹם", "גָּדוֹל", "אָדָם"],
        )
        target = suffix("שָׁלוֹם")
        cand = suffix("חָלוֹם")

        for _ in range(3):
            feedback_service.save_feedback(
                "שָׁלוֹם", "חָלוֹם", reason="worse_rhyme",
                target_key=str(target), suggested_key=str(cand), rhyme_level=1,
            )
        learning_service.analyze_and_save()

        result = sv.build_candidates(["x"], 0, "שָׁלוֹם", target, 3, set())
        assert "חָלוֹם" not in result, (
            "המילה נלמדה כ'זוג רע' אבל חזרה בדלת האחורית - "
            "כנראה דרך ה-fallback שלא בדק bad_pair_words"
        )
