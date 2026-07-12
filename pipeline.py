"""
Orchestration: ניתוח שיר, בניית הצעות, רינדור HTML.
"""
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.improved_suggestion_service import vocalize_lines, _vocalize
from services.phonetic_rhyme_checker import get_phonetic_suffix, compare_phonetic_suffixes
from services.line_generator import rewrite_line_for_rhyme
from services.feedback_service import get_rejected_words
from services.bert_service import get_fill_mask_suggestions
from services.improved_suggestion_service import _is_valid_hebrew_word, _letters_only



LEVEL_LABEL = {
    1: ('חרוז מושלם',    '#b3ffb3', '#1e601e'),
    2: ('חרוז טוב',      '#d4f7d4', '#1e601e'),
    3: ('עיצור משותף',   '#ffcc99', '#333'),
    4: ('תנועה משותפת',  '#ffe0b3', '#333'),
    5: ('חרוז חסר',      '#ff9999', '#333'),
}


def _get_line_suggestions(
    lines: list[str],
    line_idx: int,
    bad_word: str,
    target_suffix: tuple,
    rejected: set,
    orig_level: int = 5,
) -> list[dict]:
    
    suggestions = []
    seen_words = set()
    bad_letters = _letters_only(bad_word)

    if orig_level <= 1:
        return []
    raw = get_fill_mask_suggestions(lines, line_idx, bad_word, top_k=50)
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
        if level < orig_level:
            words = lines[line_idx].split()
            new_line = ' '.join(words[:-1] + [word]) if words else word
            suggestions.append({'line': new_line, 'last_word': word, 'level': level, 'method': 'last_word'})

    if len(suggestions) < 3:
        extended = rewrite_line_for_rhyme(lines[line_idx], target_suffix, num_suggestions=5)
        for sug in extended:
            w = sug.get('last_word', '')
            if sug.get('method') == 'הוספת מילה' and w and w not in seen_words and '[MASK]' not in sug.get('line', ''):
                seen_words.add(w)
                suggestions.append({'line': sug['line'], 'last_word': w, 'level': sug['level'], 'method': 'extend'})

    suggestions.sort(key=lambda x: x['level'])
    return suggestions[:10]


def _get_pair_suggestions_parallel(
    lines: list[str],
    idx1: int,
    idx2: int,
    suffix1: tuple,
    suffix2: tuple,
    word1: str,
    word2: str,
    rejected1: set,
    rejected2: set,
    orig_level: int = 5,
) -> tuple[list[dict], list[dict]]:
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(_get_line_suggestions, lines, idx2, word2, suffix1, rejected2, orig_level)
        f2 = ex.submit(_get_line_suggestions, lines, idx1, word1, suffix2, rejected1, orig_level)
        sug_for_line2 = f1.result()
        sug_for_line1 = f2.result()
    return sug_for_line2, sug_for_line1


def _is_aaab(stanza_analysis: dict) -> bool:
    return 'א-א-א-ב' in stanza_analysis['pattern']


def _is_bbbb(stanza_analysis: dict) -> bool:
    keys = stanza_analysis['line_keys']
    if len(keys) < 2:
        return False
    return all(RhymeChecker.rhyme_level(keys[0], k) <= 2 for k in keys[1:])


def _get_b_key(rhyme_keys: list) -> tuple | None:
    """מפתח שורה ד' (ה-B) בבית AAAB."""
    return rhyme_keys[3] if len(rhyme_keys) == 4 else None


def _analyze_poem_wide_pattern(all_stanzas: list[dict]) -> dict | None:
    """
    בדיקת תבנית AAAB ברמת השיר כולו.
    תנאים:
    - כל הבתים הם AAAB, עם אפשרות לבית BBBB אחד בלבד (פזמון)
    - ה-B חייב להיות זהה בכל הבתים AAAB
    מחזיר {'b_key': tuple, 'bbbb_stanza_idx': int|None} או None.
    """
    if len(all_stanzas) < 2:
        return None

    aaab_indices, bbbb_indices, other_indices = [], [], []
    for i, s in enumerate(all_stanzas):
        a = s['_analysis']
        if _is_aaab(a):
            aaab_indices.append(i)
        elif _is_bbbb(a):
            bbbb_indices.append(i)
        else:
            other_indices.append(i)

    if other_indices or len(bbbb_indices) > 1 or not aaab_indices:
        return None

    first_b_key = all_stanzas[aaab_indices[0]].get('b_key') or _get_b_key(all_stanzas[aaab_indices[0]]['_analysis']['line_keys'])
    if first_b_key is None:
        return None

    for i in aaab_indices[1:]:
        b_key = all_stanzas[i].get('b_key') or _get_b_key(all_stanzas[i]['_analysis']['line_keys'])
        if b_key is None or RhymeChecker.rhyme_level(first_b_key, b_key) > 2:
            return None

    return {
        'b_key': first_b_key,
        'bbbb_stanza_idx': bbbb_indices[0] if bbbb_indices else None,
    }


def _analyze_stanza(raw_stanza: str) -> dict | None:
    """ניתוח ראשוני של בית בודד — מיועד להרצה ב-thread."""
    lines = [l.strip() for l in raw_stanza.split("\n") if l.strip()]
    if not lines:
        return None
    metadata = vocalize_lines(lines)
    stanza_analysis = RhymeChecker.analyze_stanza(metadata)
    phonetic_suffixes = [
        get_phonetic_suffix(m['last_word_vocalized'], m['stress_type'])
        for m in metadata
    ]
    b_key = _get_b_key(stanza_analysis['line_keys']) if _is_aaab(stanza_analysis) else None
    return {
        'lines': lines,
        'metadata': metadata,
        'rhyme_keys': stanza_analysis['line_keys'],
        'phonetic_suffixes': phonetic_suffixes,
        'pattern': stanza_analysis['pattern'],
        '_analysis': stanza_analysis,
        'b_key': b_key,  # None אם לא AAAB
    }


def _build_stanza_suggestions(stanza: dict, poem_wide: dict | None, rejected_words: dict) -> dict:
    """קביעת זוגות חריזה ובניית הצעות לבית בודד — מיועד להרצה ב-thread."""
    lines             = stanza['lines']
    metadata          = stanza['metadata']
    phonetic_suffixes = stanza['phonetic_suffixes']
    analysis          = stanza['_analysis']

    expected_pairs = [
        (i + 1, j + 1)
        for i, j in analysis.get('expected_pairs_indices', [])
    ]

    if poem_wide:
        b_key = poem_wide['b_key']
        if _is_aaab(analysis):
            stanza_b_key = _get_b_key(stanza['rhyme_keys'])
            if stanza_b_key and RhymeChecker.rhyme_level(b_key, stanza_b_key) > 2:
                expected_pairs = [(1, 4)]
        elif _is_bbbb(analysis):
            stanza_b_key = stanza['rhyme_keys'][0] if stanza['rhyme_keys'] else None
            if stanza_b_key and RhymeChecker.rhyme_level(b_key, stanza_b_key) > 2:
                expected_pairs = [(1, j + 1) for j in range(1, len(lines))]

    orig_alerts = {}
    for line1_num, line2_num in expected_pairs:
        level = compare_phonetic_suffixes(
            phonetic_suffixes[line1_num - 1],
            phonetic_suffixes[line2_num - 1]
        )
        if level > 2:
            orig_alerts[line2_num] = {'level': level, 'lines': (line1_num, line2_num)}

    suggestions_per_line: dict[int, list[dict]] = {}
    target_suffixes: dict[int, tuple] = {}

    for line1_num, line2_num in expected_pairs:
        if line2_num not in orig_alerts:
            continue
        if orig_alerts[line2_num]['level'] <= 1:
            continue
        idx1, idx2 = line1_num - 1, line2_num - 1
        word1 = metadata[idx1]['original_word']
        word2 = metadata[idx2]['original_word']
        suffix1 = phonetic_suffixes[idx1]
        suffix2 = phonetic_suffixes[idx2]
        rejected1 = get_rejected_words(word1) | rejected_words.get(word1, set())
        rejected2 = get_rejected_words(word2) | rejected_words.get(word2, set())

        sug_line2, sug_line1 = _get_pair_suggestions_parallel(
            lines, idx1, idx2, suffix1, suffix2, word1, word2, rejected1, rejected2,
            orig_level=orig_alerts[line2_num]['level'],
        )

        best2 = sug_line2[0]['level'] if sug_line2 else 99
        best1 = sug_line1[0]['level'] if sug_line1 else 99

        if best2 <= best1:
            suggestions_per_line[line2_num] = sug_line2
            target_suffixes[line2_num] = suffix1
        else:
            suggestions_per_line[line1_num] = sug_line1
            target_suffixes[line1_num] = suffix2
            orig_alerts[line1_num] = orig_alerts.pop(line2_num)
            orig_alerts[line1_num]['lines'] = (line2_num, line1_num)

    return {
        **stanza,
        'expected_pairs':       expected_pairs,
        'orig_alerts':          orig_alerts,
        'suggestions_per_line': suggestions_per_line,
        'target_suffixes':      target_suffixes,
    }


def analyze_poem_and_get_suggestions(poem_text: str, rejected_words: dict = None) -> list[dict] | None:
    if not poem_text.strip():
        return None
    if rejected_words is None:
        rejected_words = {}

    raw_stanzas = [s for s in poem_text.split("\n\n") if s.strip()]

    # שלב 1: ניתוח ראשוני של כל הבתים במקביל
    with ThreadPoolExecutor(max_workers=len(raw_stanzas)) as ex:
        futures = {ex.submit(_analyze_stanza, s): i for i, s in enumerate(raw_stanzas)}
        ordered = [None] * len(raw_stanzas)
        for f in as_completed(futures):
            ordered[futures[f]] = f.result()
    all_stanzas = [s for s in ordered if s is not None]

    # שלב 2: בדיקת תבנית AAAB ברמת השיר כולו
    poem_wide = _analyze_poem_wide_pattern(all_stanzas)

    # שלב 3: בניית הצעות לכל הבתים במקביל
    with ThreadPoolExecutor(max_workers=len(all_stanzas)) as ex:
        futures = {ex.submit(_build_stanza_suggestions, s, poem_wide, rejected_words): i
                   for i, s in enumerate(all_stanzas)}
        ordered = [None] * len(all_stanzas)
        for f in as_completed(futures):
            ordered[futures[f]] = f.result()

    return [s for s in ordered if s is not None]


def render_poem_html(all_stanzas: list[dict], suggestion_index: int, rejected_words: dict = None) -> tuple[str, bool, list[dict], list[dict]]:
    if rejected_words is None:
        rejected_words = {}
    stanzas_html = []
    has_replacements = False
    replacements_info: list[dict] = []
    fallback_info: list[dict] = []  # מילים שנפסלו כשאין הצעות חדשות

    for stanza in all_stanzas:
        lines                = stanza['lines']
        metadata             = stanza['metadata']
        expected_pairs       = stanza['expected_pairs']
        orig_alerts          = stanza['orig_alerts']
        suggestions_per_line = stanza['suggestions_per_line']
        target_suffixes      = stanza['target_suffixes']
        phonetic_suffixes    = stanza['phonetic_suffixes']

        display_lines = list(lines)
        eval_lines    = list(lines)
        badges: dict[int, str] = {}

        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            line1_idx = line1_num - 1

            # מצא איזו שורה בזוג יש לה alert והצעות
            alert_line = line2_num if line2_num in orig_alerts else (line1_num if line1_num in orig_alerts else None)
            if alert_line is None:
                continue
            alert_idx = alert_line - 1

            candidates = suggestions_per_line.get(alert_line, [])
            if not candidates:
                continue

            bad_word     = metadata[alert_idx]['original_word']
            rejected_set = rejected_words.get(bad_word, set())
            all_rejected_candidates = [c for c in candidates if c['last_word'] in rejected_set]
            candidates = [c for c in candidates if c['last_word'] not in rejected_set]
            if not candidates:
                if all_rejected_candidates:
                    fallback_info.append({
                        'line_num': alert_line,
                        'original_word': bad_word,
                        'original_line': lines[alert_idx],
                        'rejected_suggestions': [c['last_word'] for c in all_rejected_candidates],
                    })
                continue

            sug        = candidates[suggestion_index % len(candidates)]
            orig_level = orig_alerts[alert_line]['level']

            sug_voc    = _vocalize(sug['last_word'])
            sug_suffix = get_phonetic_suffix(sug_voc, StressDetector.detect_stress(sug_voc))
            target_suf = target_suffixes.get(alert_line, ())
            new_level  = compare_phonetic_suffixes(sug_suffix, target_suf)

            if new_level >= orig_level:
                continue

            has_replacements = True
            replacements_info.append({
                'line2_num':      alert_line,
                'original_word':  bad_word,
                'original_line':  lines[alert_idx],
                'suggested_word': sug['last_word'],
                'suggested_line': sug['line'],
                'method':         sug['method'],
                'target_key':     str(target_suf),
                'suggested_key':  str(sug_suffix),
                'rhyme_level':    new_level,
            })

            prefix = sug['line'].rsplit(sug['last_word'], 1)[0]
            marked = (
                f"<mark style='background-color:#ffffcc;font-weight:bold;"
                f"color:#d9381e;padding:0 4px;border-radius:3px;'>{sug['last_word']}</mark>"
            )
            display_lines[alert_idx] = prefix + marked
            eval_lines[alert_idx]    = sug['line']

        new_metadata = vocalize_lines(eval_lines)
        new_suffixes = [
            get_phonetic_suffix(m['last_word_vocalized'], m['stress_type'])
            for m in new_metadata
        ]

        for line1_num, line2_num in expected_pairs:
            line2_idx    = line2_num - 1
            had_alert    = line2_num in orig_alerts or line1_num in orig_alerts
            was_changed2 = eval_lines[line2_idx] != lines[line2_idx]
            was_changed1 = eval_lines[line1_num - 1] != lines[line1_num - 1]

            if not had_alert and not was_changed2 and not was_changed1:
                continue

            suf1  = new_suffixes[line1_num - 1]
            suf2  = new_suffixes[line2_idx]
            # שימוש ב-rhyme_level ישירות כדי שהסיווג יהיה מדויק לפי הלוגיקה הנכונה
            k1    = RhymeChecker.extract_rhyme_key(
                new_metadata[line1_num - 1]['last_word_vocalized'],
                new_metadata[line1_num - 1]['stress_type']
            )
            k2    = RhymeChecker.extract_rhyme_key(
                new_metadata[line2_idx]['last_word_vocalized'],
                new_metadata[line2_idx]['stress_type']
            )
            level = RhymeChecker.rhyme_level(k1, k2)
            label, color, txt = LEVEL_LABEL.get(level, ('חרוז חסר', '#ff9999', '#333'))

            if level > 2:
                badge = (
                    f" <span style='background-color:{color};font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:{txt};'>"
                    f"⚠️ {label} ({line1_num}-{line2_num})</span>"
                )
            elif was_changed2 or was_changed1:
                badge = (
                    f" <span style='background-color:#b3d9ff;font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:#004085;'>"
                    f"🚀 חרוז שופר! {label} ({line1_num}-{line2_num})</span>"
                )
            else:
                badge = (
                    f" <span style='background-color:{color};font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:{txt};'>"
                    f"✨ {label} ({line1_num}-{line2_num})</span>"
                )
            badges[line1_num] = badge
            badges[line2_num] = badge

        rows = [f"{display_lines[i]}{badges.get(i+1,'')}" for i in range(len(display_lines))]
        stanzas_html.append(f"<p style='margin-bottom:25px;'>{'<br>'.join(rows)}</p>")

    html = (
        "<div style='direction:rtl;text-align:right;line-height:2.0;font-size:16px;'>"
        + "".join(stanzas_html)
        + "</div>"
    )
    return html, has_replacements, replacements_info, fallback_info
