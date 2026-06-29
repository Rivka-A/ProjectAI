"""
בניית רשימת candidates לכל שורה בעייתית.
כלל: הצעה נכנסת רק אם רמת החרוז שלה <= רמת המקור (כלומר לא גרועה ממנו).
עדיפות: חרוז מושלם (1) > עיצור משותף (2) > תנועה משותפת (3).
"""
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.nakdan_service import NakdanService
from services.bert_service import get_fill_mask_suggestions
from services.learning_service import get_min_acceptable_level, is_bad_pair

_nakdan = NakdanService()


# תווי ניקוד עברי
_NIQUD = set('\u05B0\u05B1\u05B2\u05B3\u05B4\u05B5\u05B6\u05B7\u05B8\u05B9\u05BA\u05BB\u05BC\u05BD\u05C1\u05C2')


def is_vocalized(word: str) -> bool:
    """מחזיר True אם המילה כבר מכילה ניקוד."""
    return any(c in _NIQUD for c in word)


def _build_from_option(res: list, option_idx: int) -> str:
    """בונה מחרוזת מנוקדת מתוך אפשרות מספר option_idx של תשובת הנקדן."""
    chars = []
    for entry in res:
        if not isinstance(entry, dict):
            chars.append(str(entry))
            continue
        options = entry.get('options', [])
        if options and option_idx < len(options):
            opt = options[option_idx]
            chars.append(opt.get('w', '') if isinstance(opt, dict) else opt)
        elif options:
            opt = options[0]
            chars.append(opt.get('w', '') if isinstance(opt, dict) else opt)
        else:
            chars.append(entry.get('char', ''))
    return "".join(chars).strip()


def _vocalize(word: str) -> str:
    """
    מנקד מילה בודדת.
    - אם המילה כבר מנוקדת — מחזיר אותה כמו שהיא.
    - אחרת שולח לנקדן ומשתמש ב-voting: מחשב מפתח חרוז לכל אפשרות
      ומחזיר את הניקוד שמפתח החרוז שלו הכי נפוץ (קונסנזוס).
    """
    if not word.strip():
        return word
    if is_vocalized(word):
        return word

    res = _nakdan.get_vocalized_text(word)
    if not res or not isinstance(res, list):
        return word

    # מצא את מספר האפשרויות המקסימלי
    max_opts = max(
        (len(e.get('options', [])) for e in res if isinstance(e, dict)),
        default=1
    )

    # בנה את כל הגרסאות המנוקדות האפשריות
    candidates = [_build_from_option(res, i) for i in range(max_opts)]
    candidates = [c for c in candidates if c]
    if not candidates:
        return word
    if len(candidates) == 1:
        return candidates[0]

    # Voting: חשב מפתח חרוז לכל אפשרות ובחר את המפתח הנפוץ ביותר
    from collections import Counter
    key_to_voc: dict[str, str] = {}
    keys = []
    for voc in candidates:
        k = RhymeChecker.extract_rhyme_key(voc, StressDetector.detect_stress(voc))
        keys.append(k)
        if k not in key_to_voc:
            key_to_voc[k] = voc

    best_key = Counter(keys).most_common(1)[0][0]
    return key_to_voc[best_key]


def _letters_only(text: str) -> str:
    return "".join(c for c in text if '\u05D0' <= c <= '\u05EA')


def build_candidates(
    lines: list[str],
    line2_idx: int,
    bad_word: str,
    target_key: str,
    orig_level: int,
    rejected_words: set[str],
) -> list[str]:
    """
    בונה רשימת מילים מוצעות לשורה line2_idx.
    - מסנן מילים ב-rejected_words (נדחו ע"י המשתמש)
    - מסנן הצעות שרמת החרוז שלהן גרועה מ-orig_level
    - ממיין לפי עדיפות: רמה 1 > 2 > 3
    """
    raw = get_fill_mask_suggestions(lines, line2_idx, bad_word)
    bad_letters = _letters_only(bad_word)

    # רמה מינימלית שנלמדה מהמשובים — אבל לא להחמיר מעבר לרמת המקור
    learned_min_level = get_min_acceptable_level()
    effective_max_level = min(orig_level, learned_min_level) if orig_level < 5 else learned_min_level

    buckets: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    seen: set[str] = set()

    for word in raw:
        if _letters_only(word) == bad_letters:
            continue
        if word in seen or word in rejected_words:
            continue
        seen.add(word)

        voc = _vocalize(word)
        key = RhymeChecker.extract_rhyme_key(voc, StressDetector.detect_stress(voc))
        level = RhymeChecker.rhyme_level(target_key, key)

        # סנן זוגות שנלמדו כבעייתיים
        if is_bad_pair(str(target_key), str(key)):
            continue

        if level <= effective_max_level:
            buckets.setdefault(level, []).append(word)

    combined = buckets.get(1, []) + buckets.get(2, []) + buckets.get(3, []) + buckets.get(4, [])

    # אם אין מספיק — הוסף "שאר" שעדיין לא יותר גרועים מרמה 4 (כלומר הכל)
    if len(combined) < 5:
        for word in raw:
            if _letters_only(word) == bad_letters or word in seen or word in rejected_words:
                continue
            seen.add(word)
            combined.append(word)
            if len(combined) >= 5:
                break

    return combined


def vocalize_lines(lines: list[str]) -> list[dict]:
    """בונה מטא-דאטה מנוקד לכל שורה (מילה אחרונה)."""
    metadata = []
    for line in lines:
        words = line.split()
        last = words[-1] if words else ""
        voc = _vocalize(last)
        metadata.append({
            'original_word': last,
            'last_word_vocalized': voc,
            'stress_type': StressDetector.detect_stress(voc),
            'was_vocalized': is_vocalized(last),
        })
    return metadata
