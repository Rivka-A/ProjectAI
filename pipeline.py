"""
Orchestration: ניתוח שיר, בניית הצעות, רינדור HTML.
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.improved_suggestion_service import vocalize_lines, _vocalize
from services.phonetic_rhyme_checker import get_phonetic_suffix, compare_phonetic_suffixes
from services.line_generator import rewrite_line_for_rhyme
from services.feedback_service import get_rejected_words


def _get_rhyme_pairs(num_lines: int, pattern: str) -> list[tuple[int, int]]:
    """מחזיר זוגות חריזה לפי תבנית."""
    if num_lines == 4:
        if 'ABBA' in pattern or 'א-ב-ב-א' in pattern:
            return [(1, 4), (2, 3)]
        if 'ABAB' in pattern or 'א-ב-א-ב' in pattern:
            return [(1, 3), (2, 4)]
        if 'AABB' in pattern or 'א-א-ב-ב' in pattern:
            return [(1, 2), (3, 4)]
    return [(i, i + 1) for i in range(1, num_lines)]


def _detect_pattern(line_keys: list) -> str:
    """זהה תבנית חריזה."""
    if len(line_keys) != 4:
        return 'חופשית'

    def rhymes(i, j):
        return RhymeChecker.rhyme_level(line_keys[i], line_keys[j]) <= 2

    score_aabb = rhymes(0, 1) + rhymes(2, 3)
    score_abab = rhymes(0, 2) + rhymes(1, 3)
    score_abba = rhymes(0, 3) + rhymes(1, 2)

    best = max(score_aabb, score_abab, score_abba)
    if best == 0:
        return 'חופשית'
    if score_abba == best:
        return 'ABBA'
    if score_abab == best:
        return 'ABAB'
    return 'AABB'


def _get_line_suggestions(
    lines: list[str],
    line_idx: int,
    bad_word: str,
    target_suffix: tuple,
    rejected: set,
) -> list[dict]:
    """
    קבל הצעות לשורה - כולל שינוי שורה שלמה.
    מחזיר רשימה של {'line': str, 'last_word': str, 'level': int, 'method': str}
    """
    from services.bert_service import get_fill_mask_suggestions
    from services.improved_suggestion_service import _vocalize, _is_valid_hebrew_word, _letters_only

    suggestions = []
    seen_words = set()
    bad_letters = _letters_only(bad_word)

    # שיטה 1: החלפת מילה אחרונה
    raw = get_fill_mask_suggestions(lines, line_idx, bad_word, top_k=40)
    for word in raw:
        if not word or word in seen_words or word in rejected:
            continue
        if _letters_only(word) == bad_letters:
            continue
        if not _is_valid_hebrew_word(word):
            continue
        seen_words.add(word)

        voc = _vocalize(word)
        suffix = get_phonetic_suffix(voc, StressDetector.detect_stress(voc))
        level = compare_phonetic_suffixes(suffix, target_suffix)

        if level <= 2:
            words = lines[line_idx].split()
            new_line = ' '.join(words[:-1] + [word]) if words else word
            suggestions.append({
                'line': new_line,
                'last_word': word,
                'level': level,
                'method': 'last_word',
            })

    # שיטה 2: הוספת מילה בסוף (אם אין מספיק הצעות)
    if len(suggestions) < 3:
        extended = rewrite_line_for_rhyme(lines[line_idx], target_suffix, num_suggestions=5)
        for sug in extended:
            if sug.get('method') == 'הוספת מילה' and sug['last_word'] not in seen_words:
                seen_words.add(sug['last_word'])
                suggestions.append({
                    'line': sug['line'],
                    'last_word': sug['last_word'],
                    'level': sug['level'],
                    'method': 'extend',
                })

    # מיין לפי רמת חרוז
    suggestions.sort(key=lambda x: x['level'])
    return suggestions[:10]


def analyze_poem_and_get_suggestions(poem_text: str, rejected_words: dict = None) -> list[dict] | None:
    if not poem_text.strip():
        return None
    if rejected_words is None:
        rejected_words = {}

    all_stanzas = []
    for raw_stanza in poem_text.split("\n\n"):
        lines = [l.strip() for l in raw_stanza.split("\n") if l.strip()]
        if not lines:
            continue

        metadata = vocalize_lines(lines)

        # חשב מפתחות חרוז וסיומות פונטיות
        rhyme_keys = [
            RhymeChecker.extract_rhyme_key(m['last_word_vocalized'], m['stress_type'])
            for m in metadata
        ]
        phonetic_suffixes = [
            get_phonetic_suffix(m['last_word_vocalized'], m['stress_type'])
            for m in metadata
        ]

        # זהה תבנית
        pattern = _detect_pattern(rhyme_keys)
        expected_pairs = _get_rhyme_pairs(len(lines), pattern)

        # מצא בעיות חריזה
        orig_alerts = {}
        for line1_num, line2_num in expected_pairs:
            idx1, idx2 = line1_num - 1, line2_num - 1
            suffix1 = phonetic_suffixes[idx1]
            suffix2 = phonetic_suffixes[idx2]
            level = compare_phonetic_suffixes(suffix1, suffix2)
            if level > 2:
                orig_alerts[line2_num] = {
                    'level': level,
                    'lines': (line1_num, line2_num),
                }

        # בנה הצעות
        suggestions_per_line: dict[int, list[dict]] = {}
        target_suffixes: dict[int, tuple] = {}

        for line1_num, line2_num in expected_pairs:
            if line2_num not in orig_alerts:
                continue
            line2_idx = line2_num - 1
            bad_word = metadata[line2_idx]['original_word']
            target_suffix = phonetic_suffixes[line1_num - 1]
            rejected = get_rejected_words(bad_word) | rejected_words.get(bad_word, set())

            candidates = _get_line_suggestions(
                lines, line2_idx, bad_word, target_suffix, rejected
            )
            suggestions_per_line[line2_num] = candidates
            target_suffixes[line2_num] = target_suffix

        all_stanzas.append({
            'lines': lines,
            'metadata': metadata,
            'rhyme_keys': rhyme_keys,
            'phonetic_suffixes': phonetic_suffixes,
            'pattern': pattern,
            'expected_pairs': expected_pairs,
            'orig_alerts': orig_alerts,
            'suggestions_per_line': suggestions_per_line,
            'target_suffixes': target_suffixes,
        })

    return all_stanzas


def render_poem_html(all_stanzas: list[dict], suggestion_index: int, rejected_words: dict = None) -> tuple[str, bool, list[dict]]:
    if rejected_words is None:
        rejected_words = {}
    stanzas_html = []
    has_replacements = False
    replacements_info: list[dict] = []

    for stanza in all_stanzas:
        lines               = stanza['lines']
        metadata            = stanza['metadata']
        expected_pairs      = stanza['expected_pairs']
        orig_alerts         = stanza['orig_alerts']
        suggestions_per_line = stanza['suggestions_per_line']
        target_suffixes     = stanza['target_suffixes']
        phonetic_suffixes   = stanza['phonetic_suffixes']

        display_lines = list(lines)
        eval_lines    = list(lines)
        badges: dict[int, str] = {}

        # החל הצעות
        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            if line2_num not in orig_alerts:
                continue
            candidates = suggestions_per_line.get(line2_num, [])
            if not candidates:
                continue

            bad_word   = metadata[line2_idx]['original_word']
            rejected_set = rejected_words.get(bad_word, set())
            candidates = [c for c in candidates if c['last_word'] not in rejected_set]
            if not candidates:
                continue

            sug        = candidates[suggestion_index % len(candidates)]
            orig_level = orig_alerts[line2_num]['level']

            # בדוק שההצעה משפרת
            sug_voc    = _vocalize(sug['last_word'])
            sug_suffix = get_phonetic_suffix(sug_voc, StressDetector.detect_stress(sug_voc))
            target_suf = target_suffixes.get(line2_num, ())
            new_level  = compare_phonetic_suffixes(sug_suffix, target_suf)

            if new_level >= orig_level:
                continue

            has_replacements = True
            replacements_info.append({
                'line2_num':      line2_num,
                'original_word':  bad_word,
                'original_line':  lines[line2_idx],
                'suggested_word': sug['last_word'],
                'suggested_line': sug['line'],
                'method':         sug['method'],
                'target_key':     str(target_suf),
                'suggested_key':  str(sug_suffix),
                'rhyme_level':    new_level,
            })

            # הצג את השורה המשופרת עם הדגשה על המילה האחרונה
            prefix = sug['line'].rsplit(sug['last_word'], 1)[0]
            marked = (
                f"<mark style='background-color:#ffffcc;font-weight:bold;"
                f"color:#d9381e;padding:0 4px;border-radius:3px;'>{sug['last_word']}</mark>"
            )
            display_lines[line2_idx] = prefix + marked
            eval_lines[line2_idx]    = sug['line']

        # חשב badges
        new_metadata = vocalize_lines(eval_lines)
        new_suffixes = [
            get_phonetic_suffix(m['last_word_vocalized'], m['stress_type'])
            for m in new_metadata
        ]

        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            had_alert   = line2_num in orig_alerts
            was_changed = eval_lines[line2_idx] != lines[line2_idx]

            if not had_alert and not was_changed:
                continue

            suf1 = new_suffixes[line1_num - 1]
            suf2 = new_suffixes[line2_idx]
            level = compare_phonetic_suffixes(suf1, suf2)

            if level > 2:
                color = {3: '#ffcc99', 4: '#ffe0b3'}.get(level, '#ff9999')
                label = {3: 'תנועה משותפת', 4: 'עיצור משותף'}.get(level, 'חרוז חסר')
                badges[line2_num] = (
                    f" <span style='background-color:{color};font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:#333;'>"
                    f"⚠️ {label} ({line1_num}-{line2_num})</span>"
                )
            elif was_changed:
                badges[line2_num] = (
                    f" <span style='background-color:#b3d9ff;font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:#004085;'>"
                    f"🚀 חרוז שופר! ({line1_num}-{line2_num})</span>"
                )
            else:
                badges[line2_num] = (
                    f" <span style='background-color:#b3ffb3;font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:#1e601e;'>"
                    f"✨ חרוז מושלם ({line1_num}-{line2_num})</span>"
                )

        rows = [f"{display_lines[i]}{badges.get(i+1,'')}" for i in range(len(display_lines))]
        stanzas_html.append(f"<p style='margin-bottom:25px;'>{'<br>'.join(rows)}</p>")

    html = (
        "<div style='direction:rtl;text-align:right;line-height:2.0;font-size:16px;'>"
        + "".join(stanzas_html)
        + "</div>"
    )
    return html, has_replacements, replacements_info
