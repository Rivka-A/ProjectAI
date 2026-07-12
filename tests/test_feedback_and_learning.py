# -*- coding: utf-8 -*-
"""
טסטים ל-feedback_service ול-learning_service.

חשוב: המודולים האלה כותבים לקבצים אמיתיים (feedback_log.jsonl,
learned_rules.json) לפי נתיב יחסי ל-BASE_DIR. הפיקסצ'ר
`isolated_feedback` (ב-conftest.py) מפנה אותם זמנית ל-tmp_path כדי
שהטסטים לא יכתבו לקובץ האמיתי ולא יזהמו ריצות אחרות.
"""
import pytest


class TestSaveAndLoadFeedback:
    def test_round_trip(self, isolated_feedback):
        feedback_service, _ = isolated_feedback
        feedback_service.save_feedback(
            original_word="שָׁלוֹם",
            suggested_word="חָלוֹם",
            reason="approved",
            target_key="k1",
            suggested_key="k1",
            rhyme_level=1,
        )
        entries = feedback_service.load_all_feedback()
        assert len(entries) == 1
        assert entries[0]["original"] == "שָׁלוֹם"
        assert entries[0]["reason"] == "approved"

    def test_load_returns_empty_list_when_no_file(self, isolated_feedback):
        feedback_service, _ = isolated_feedback
        assert feedback_service.load_all_feedback() == []

    def test_corrupted_line_is_skipped_not_crashed(self, isolated_feedback, tmp_path):
        feedback_service, _ = isolated_feedback
        with open(feedback_service.LOG_PATH, "w", encoding="utf-8") as f:
            f.write("{not valid json\n")
            f.write('{"original": "a", "reason": "approved"}\n')
        entries = feedback_service.load_all_feedback()
        assert len(entries) == 1
        assert entries[0]["original"] == "a"

    def test_get_rejected_words_excludes_approved(self, isolated_feedback):
        feedback_service, _ = isolated_feedback
        feedback_service.save_feedback("בַּד", "רַד", reason="worse_rhyme")
        feedback_service.save_feedback("בַּד", "גַּד", reason="approved")
        feedback_service.save_feedback("בַּד", "מַד", reason="dislike")
        rejected = feedback_service.get_rejected_words("בַּד")
        assert rejected == {"רַד", "מַד"}


class TestLearningServiceThresholds:
    def _feed(self, feedback_service, n_shown_level2, n_rejected_level2):
        """עוזר: מזין n_shown הצגות ברמה 2, מתוכן n_rejected נדחות."""
        for i in range(n_rejected_level2):
            feedback_service.save_feedback(
                f"orig{i}", f"sug{i}", reason="worse_rhyme", rhyme_level=2,
            )
        for i in range(n_shown_level2 - n_rejected_level2):
            feedback_service.save_feedback(
                f"orig_ok{i}", f"sug_ok{i}", reason="approved", rhyme_level=2,
            )

    def test_no_feedback_returns_empty_rules(self, isolated_feedback):
        _, learning_service = isolated_feedback
        assert learning_service.analyze_and_save() == {}

    def test_default_min_acceptable_level_is_3_when_no_rules(self, isolated_feedback):
        _, learning_service = isolated_feedback
        assert learning_service.get_min_acceptable_level() == 3

    def test_level_becomes_bad_when_rejection_rate_high_enough(self, isolated_feedback):
        feedback_service, learning_service = isolated_feedback
        # 4 הצגות ברמה 2, 3 מתוכן נדחו (75% >= 50% הסף, וגם >= 2 דחיות)
        self._feed(feedback_service, n_shown_level2=4, n_rejected_level2=3)
        rules = learning_service.analyze_and_save()
        assert 2 in rules["bad_rhyme_levels"]
        # מכיוון ש-2 נדחה -> min_acceptable_level יורד ל-1
        assert learning_service.get_min_acceptable_level() == 1

    def test_level_not_flagged_when_below_min_rejections(self, isolated_feedback):
        feedback_service, learning_service = isolated_feedback
        # רק דחייה אחת - מתחת ל-MIN_REJECTIONS (2) -> לא אמור להיכנס לכלל
        feedback_service.save_feedback("a", "b", reason="worse_rhyme", rhyme_level=2)
        rules = learning_service.analyze_and_save()
        assert 2 not in rules.get("bad_rhyme_levels", [])
        assert learning_service.get_min_acceptable_level() == 3

    def test_is_bad_pair_reflects_learned_rules(self, isolated_feedback):
        feedback_service, learning_service = isolated_feedback
        for _ in range(3):
            feedback_service.save_feedback(
                "orig", "sug", reason="worse_rhyme",
                target_key="TK", suggested_key="SK", rhyme_level=2,
            )
        learning_service.analyze_and_save()
        assert learning_service.is_bad_pair("TK", "SK") is True
        assert learning_service.is_bad_pair("TK", "OTHER") is False

    def test_bad_context_words_collected(self, isolated_feedback):
        feedback_service, learning_service = isolated_feedback
        for _ in range(2):
            feedback_service.save_feedback(
                "orig", "לא_מתאים", reason="bad_context",
            )
        rules = learning_service.analyze_and_save()
        assert "לא_מתאים" in rules["context_rejected_words"]

    def test_approval_rate_computed_correctly(self, isolated_feedback):
        feedback_service, learning_service = isolated_feedback
        feedback_service.save_feedback("a", "b", reason="approved")
        feedback_service.save_feedback("a", "c", reason="dislike")
        rules = learning_service.analyze_and_save()
        assert rules["approval_rate"] == 0.5
        assert rules["total_feedback"] == 2
