"""
Orchestration: ניתוח שיר, בניית הצעות, רינדור HTML.
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.suggestion_service import build_candidates, vocalize_lines, _vocalize
from services.feedback_service import get_rejected_words


def _get_expected_pairs(num_lines: int, pattern: str) -> list[tuple[int, int]]:
    if num_lines == 4:
        if "א-ב-א-ב" in pattern: return [(1, 3), (2, 4)]
        if "א-ב-ב-א" in pattern: return [(1, 4), (2, 3)]
        if "א-א-ב-ב" in pattern: return [(1, 2), (3, 4)]
        return [(1, 2), (3, 4)]  # ברירת מחדל
    return [(i, i + 1) for i in range(1, num_lines)]


def analyze_poem_and_get_suggestions(poem_text: str) -> list[dict] | None:
    if not poem_text.strip():
        return None

    all_stanzas = []
    for raw_stanza in poem_text.split("\n\n"):
        lines = [l.strip() for l in raw_stanza.split("\n") if l.strip()]
        if not lines:
            continue

        orig_metadata = vocalize_lines(lines)
        orig_analysis = RhymeChecker.analyze_stanza(orig_metadata)
        orig_alerts = {
            alert["lines"][1]: alert
            for alert in orig_analysis.get("alerts", [])
            if len(alert.get("lines", ())) == 2
        }
        expected_pairs = _get_expected_pairs(len(lines), orig_analysis.get("pattern", ""))

        suggestions_per_line: dict[int, list[str]] = {}
        orig_levels: dict[int, int] = {}
        target_keys: dict[int, str] = {}

        for line1_num, line2_num in expected_pairs:
            if line2_num not in orig_alerts:
                continue
            line2_idx = line2_num - 1
            bad_word = orig_metadata[line2_idx]["original_word"]
            target_key = orig_analysis["line_keys"][line1_num - 1]
            orig_level = orig_alerts[line2_num].get("level", 5)
            rejected = get_rejected_words(bad_word)

            candidates = build_candidates(lines, line2_idx, bad_word, target_key, orig_level, rejected)
            suggestions_per_line[line2_num] = candidates
            orig_levels[line2_num] = orig_level
            target_keys[line2_num] = target_key

        all_stanzas.append({
            "lines": lines,
            "orig_metadata": orig_metadata,
            "orig_analysis": orig_analysis,
            "expected_pairs": expected_pairs,
            "orig_alerts": orig_alerts,
            "suggestions_per_line": suggestions_per_line,
            "orig_levels": orig_levels,
            "target_keys": target_keys,
        })

    return all_stanzas


def render_poem_html(all_stanzas: list[dict], suggestion_index: int) -> tuple[str, bool, list[dict]]:
    """
    מרנדר HTML לפי suggestion_index.
    replacements_info כולל גם target_key, suggested_key, rhyme_level לצורך למידה.
    """
    stanzas_html = []
    has_replacements = False
    replacements_info: list[dict] = []

    for stanza in all_stanzas:
        lines          = stanza["lines"]
        orig_metadata  = stanza["orig_metadata"]
        expected_pairs = stanza["expected_pairs"]
        orig_alerts    = stanza["orig_alerts"]
        suggestions_per_line = stanza["suggestions_per_line"]
        target_keys    = stanza.get("target_keys", {})

        display_lines = list(lines)
        eval_lines    = list(lines)
        badges: dict[int, str] = {}

        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            if line2_num not in orig_alerts:
                continue
            candidates = suggestions_per_line.get(line2_num, [])
            if not candidates:
                continue

            bad_word   = orig_metadata[line2_idx]["original_word"]
            suggestion = candidates[suggestion_index % len(candidates)]
            target_key = target_keys.get(line2_num, ())
            orig_level = stanza.get("orig_levels", {}).get(line2_num, 5)

            # חישוב מפתח ורמה של ההצעה
            sug_voc = _vocalize(suggestion)
            sug_key = RhymeChecker.extract_rhyme_key(sug_voc, StressDetector.detect_stress(sug_voc))
            rhyme_lvl = RhymeChecker.rhyme_level(target_key, sug_key)

            # אם ההצעה לא משפרת את החרוז — דלג עליה
            if rhyme_lvl >= orig_level:
                continue

            has_replacements = True
            replacements_info.append({
                "line2_num":     line2_num,
                "original_word": bad_word,
                "suggested_word": suggestion,
                "target_key":    target_key,
                "suggested_key": sug_key,
                "rhyme_level":   rhyme_lvl,
            })

            prefix = lines[line2_idx].rsplit(bad_word, 1)[0]
            marked = (
                f"<mark style='background-color:#ffffcc;font-weight:bold;"
                f"color:#d9381e;padding:0 4px;border-radius:3px;'>{suggestion}</mark>"
            )
            display_lines[line2_idx] = prefix + marked
            eval_lines[line2_idx]    = prefix + suggestion

        # ריצה שנייה לאימות
        new_metadata = vocalize_lines(eval_lines)
        new_analysis = RhymeChecker.analyze_stanza(new_metadata)
        new_alerts = {
            a["lines"][1]: a
            for a in new_analysis.get("alerts", [])
            if len(a.get("lines", ())) == 2
        }

        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            if line2_num in new_alerts:
                level = new_alerts[line2_num].get("level", 5)
                atype = new_alerts[line2_num].get("type", "חרוז חסר")
                color = {2: '#d4edda', 3: '#ffcc99', 4: '#ffe0b3', 5: '#ff9999'}.get(level, '#ff9999')
                badges[line2_num] = (
                    f" <span style='background-color:{color};font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:#333;'>"
                    f"⚠️ {atype} (צמד {line1_num}-{line2_num})</span>"
                )
            elif eval_lines[line2_idx] != lines[line2_idx]:
                badges[line2_num] = (
                    f" <span style='background-color:#b3d9ff;font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:#004085;'>"
                    f"🚀 חרוז שופר! (צמד {line1_num}-{line2_num})</span>"
                )
            else:
                badges[line2_num] = (
                    f" <span style='background-color:#b3ffb3;font-size:10px;"
                    f"padding:1px 5px;border-radius:3px;font-weight:bold;color:#1e601e;'>"
                    f"✨ חרוז מושלם (צמד {line1_num}-{line2_num})</span>"
                )

        rows = [f"{display_lines[i]}{badges.get(i+1,'')}" for i in range(len(display_lines))]
        stanzas_html.append(f"<p style='margin-bottom:25px;'>{'<br>'.join(rows)}</p>")

    html = (
        "<div style='direction:rtl;text-align:right;line-height:2.0;font-size:16px;'>"
        + "".join(stanzas_html)
        + "</div>"
    )
    return html, has_replacements, replacements_info
