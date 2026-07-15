"""
שירות הצעות משופר - סינון וסידור הצעות לפי חריזה.
"""
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.nakdan_service import NakdanService
from services.bert_service import get_fill_mask_suggestions, get_contextual_suggestions
from services.learning_service import get_min_acceptable_level, is_bad_pair

_nakdan = NakdanService()

_NIQUD = set('\u05B0\u05B1\u05B2\u05B3\u05B4\u05B5\u05B6\u05B7\u05B8\u05B9\u05BA\u05BB\u05BC\u05BD\u05C1\u05C2')


def is_vocalized(word: str) -> bool:
    return any(c in _NIQUD for c in word)


def _build_from_option(res: list, option_idx: int) -> str:
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
    if not word.strip():
        return word
    if is_vocalized(word):
        return word

    try:
        res = _nakdan.get_vocalized_text(word)
    except Exception as e:
        print(f"[NAKDAN ERROR] נקדן נפל על המילה '{word}': {e}")
        return word
    if not res or not isinstance(res, list):
        return word

    max_opts = max(
        (len(e.get('options', [])) for e in res if isinstance(e, dict)),
        default=1
    )

    candidates = [_build_from_option(res, i) for i in range(max_opts)]
    candidates = [c for c in candidates if c]
    if not candidates:
        return word
    if len(candidates) == 1:
        return candidates[0]

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


def _is_valid_hebrew_word(word: str) -> bool:
    if word.startswith('##'):
        return False
    letters = _letters_only(word)
    if len(letters) < 2:
        return False
    if word[0].isdigit() or word[0].isascii():
        return False
    return True


def get_suggestions_by_rhyme(
    lines: list[str],
    line_idx: int,
    bad_word: str,
    target_key: tuple,
    orig_level: int,
    rejected_words: set[str],
) -> list[tuple[str, int]]:
    """קבל הצעות מסוננות לפי חריזה. מחזיר רשימה של (מילה, רמת_חרוז) מדורגת."""
    if line_idx >= len(lines):
        return []

    raw = get_fill_mask_suggestions(lines, line_idx, bad_word)
    if not raw:
        raw = get_contextual_suggestions(lines[line_idx], len(lines[line_idx].split()) - 1)
    if not raw:
        return []

    bad_letters = _letters_only(bad_word)
    suggestions_with_level = []
    seen = set()

    for word in raw:
        if _letters_only(word) == bad_letters or word in seen or word in rejected_words:
            continue
        if not _is_valid_hebrew_word(word):
            continue
        seen.add(word)

        voc = _vocalize(word)
        key = RhymeChecker.extract_rhyme_key(voc, StressDetector.detect_stress(voc))
        level = RhymeChecker.rhyme_level(key, target_key)

        if is_bad_pair(str(target_key), str(key)):
            continue

        if level <= 5:
            suggestions_with_level.append((word, level))

    suggestions_with_level.sort(key=lambda x: x[1])
    return suggestions_with_level[:10]


def vocalize_lines(lines: list[str]) -> list[dict]:
    """בונה מטא-דאטה מנוקד לכל שורה."""
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


def get_best_suggestion(
    lines: list[str],
    line_idx: int,
    bad_word: str,
    target_key: tuple,
) -> str:
    """
    קבל את ההצעה הטובה ביותר לשורה.
    מחזיר מילה בודדת (הטובה ביותר).
    """
    suggestions = get_suggestions_by_rhyme(
        lines, line_idx, bad_word, target_key, 4, set()
    )
    
    if suggestions:
        return suggestions[0][0]
    
    return bad_word


def improve_poem_rhyme(lines: list[str]) -> dict:
    """
    שפר את חריזת השיר.
    מחזיר דוח עם הצעות לכל שורה בעייתית.
    """
    metadata = vocalize_lines(lines)
    
    # קבל מפתחות חרוז
    rhyme_keys = []
    for meta in metadata:
        key = RhymeChecker.extract_rhyme_key(
            meta['last_word_vocalized'],
            meta['stress_type']
        )
        rhyme_keys.append(key)
    
    # זהה בעיות חריזה
    issues = []
    suggestions_map = {}
    
    for i in range(len(lines) - 1):
        for j in range(i + 1, len(lines)):
            level = RhymeChecker.rhyme_level(rhyme_keys[i], rhyme_keys[j])

            if level > 2:
                issues.append({
                    'lines': (i + 1, j + 1),
                    'words': (metadata[i]['original_word'], metadata[j]['original_word']),
                    'level': level,
                })
                
                # קבל הצעות לשורה הראשונה
                if i not in suggestions_map:
                    sugs = get_suggestions_by_rhyme(
                        lines, i, metadata[i]['original_word'], rhyme_keys[j], level, set()
                    )
                    suggestions_map[i] = sugs
    
    return {
        'lines': lines,
        'metadata': metadata,
        'issues': issues,
        'suggestions': suggestions_map,
        'num_issues': len(issues),
    }
