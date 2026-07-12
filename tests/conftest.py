import os
import sys
import importlib

import pytest

# מאפשר import של core.* ו-services.* מהשורש הפרויקט
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def isolated_feedback(tmp_path, monkeypatch):
    """
    מבודד את feedback_service ו-learning_service מקובץ ה-log/rules האמיתי,
    כדי שטסטים לא יכתבו/יקראו מהמערכת האמיתית ולא ישפיעו אחד על השני.
    מחזיר את שני המודולים (feedback, learning) אחרי ריענון עם נתיבים זמניים.
    """
    from services import feedback_service, learning_service

    log_path = tmp_path / "feedback_log.jsonl"
    rules_path = tmp_path / "learned_rules.json"

    monkeypatch.setattr(feedback_service, "LOG_PATH", str(log_path))
    monkeypatch.setattr(learning_service, "LEARNED_PATH", str(rules_path))

    return feedback_service, learning_service
