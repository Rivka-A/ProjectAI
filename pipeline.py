import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.nakdan_service import NakdanService
from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline as hf_pipeline

nakdan = NakdanService()

MODEL_DIR = os.path.join(BASE_DIR, "moduls")
_tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
_model = AutoModelForMaskedLM.from_pretrained(MODEL_DIR)
_fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer)

SKIP_TOKENS = {'.', ',', '!', '?', '[MASK]', ':', '-', '"', "'"}

def query_dicta_bert_suggestions(stanza_lines, target_line_idx, original_word):
    """ מחזירה הצעות מילים מהמודל המקומי """
    masked_lines = list(stanza_lines)
    current_line = masked_lines[target_line_idx]
    line_without_last_word = current_line.rsplit(original_word, 1)[0].strip() if original_word in current_line else current_line.strip()
    masked_lines[target_line_idx] = f"{line_without_last_word} [MASK]"
    context_text = " ".join(masked_lines)
    try:
        results = _fill_mask(context_text, top_k=30)
        return [r["token_str"] for r in results if r.get("token_str") and r["token_str"] not in SKIP_TOKENS]
    except Exception:
        return []

def get_vocalized_word_from_dicta(word):
    """ שולחת את המילה לנקדן ומחלצת את המחרוזת המנוקדת מתוך מבנה התווים של דיקטא """
    if not word.strip():
        return word
    res = nakdan.get_vocalized_text(word)
    if not res or not isinstance(res, list):
        return word
    
    # בניית המילה המנוקדת מתוך רשימת התווים/אפשרויות שחוזרת מה-API
    chars = []
    for entry in res:
        if isinstance(entry, dict):
            if 'options' in entry and entry['options']:
                opt = entry['options'][0]
                chars.append(opt.get('w', '') if isinstance(opt, dict) else opt)
            elif 'char' in entry:
                chars.append(entry['char'])
        elif isinstance(entry, str):
            chars.append(entry)
    vocalized = "".join(chars).strip()
    return vocalized if vocalized else word

def build_lines_metadata(lines_list):
    """ בניית המטא-דאטה כאשר המילה האחרונה מנוקדת מראש כדי שה-Core יזהה בעיות """
    metadata = []
    for line in lines_list:
        words = line.split()
        last_word = words[-1] if words else ""
        
        # ניקוד המילה המקורית של המשתמש
        vocalized_word = get_vocalized_word_from_dicta(last_word)
        stress_type = StressDetector.detect_stress(vocalized_word)
        
        metadata.append({
            'original_word': last_word,
            'last_word_vocalized': vocalized_word,
            'stress_type': stress_type
        })
    return metadata

def strip_to_clean_letters(text):
    """ מנקה לחלוטין את הניקוד ומשאיר רק אותיות עבריות גולמיות """
    return "".join([c for c in text if '\u05D0' <= c <= '\u05EA'])

def analyze_poem_and_get_suggestions(user_poem_text):
    """
    מנתח את השיר ומחזיר את כל ההצעות לכל שורה בעייתית.
    מוחזר: (stanzas_data, orig_html_base) כאשר stanzas_data מכיל את כל המידע לרינדור.
    """
    if not user_poem_text.strip():
        return None

    raw_stanzas = user_poem_text.split("\n\n")
    all_stanzas_data = []

    for raw_stanza in raw_stanzas:
        lines = [line.strip() for line in raw_stanza.split("\n") if line.strip()]
        if not lines:
            continue

        num_lines = len(lines)
        orig_metadata = build_lines_metadata(lines)
        orig_analysis = RhymeChecker.analyze_stanza(orig_metadata)
        orig_alerts = orig_analysis.get("alerts", [])
        orig_alerts_by_target = {alert.get("lines", ())[1]: alert for alert in orig_alerts if len(alert.get("lines", ())) == 2}

        expected_pairs = []
        if num_lines == 4:
            pattern = orig_analysis.get("pattern", "")
            if "א-ב-א-ב" in pattern: expected_pairs = [(1, 3), (2, 4)]
            elif "א-ב-ב-א" in pattern: expected_pairs = [(1, 4), (2, 3)]
            else: expected_pairs = [(1, 2), (3, 4)]
        else:
            for i in range(1, num_lines): expected_pairs.append((i, i + 1))

        # איסוף כל ההצעות לכל שורה בעייתית
        suggestions_per_line = {}
        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            if line2_num not in orig_alerts_by_target:
                continue
            bad_word = orig_metadata[line2_idx]["original_word"]
            bad_word_letters = strip_to_clean_letters(bad_word)
            raw_suggestions = query_dicta_bert_suggestions(lines, line2_idx, bad_word)
            raw_key_to_match = orig_analysis["line_keys"][line1_num - 1]
            clean_target_letters = strip_to_clean_letters(raw_key_to_match)

            full_rhyme, partial_rhyme, other = [], [], []
            seen = set()
            for sug_word in raw_suggestions:
                if strip_to_clean_letters(sug_word) == bad_word_letters or sug_word in seen:
                    continue
                seen.add(sug_word)
                sug_voc = get_vocalized_word_from_dicta(sug_word)
                sug_key = RhymeChecker.extract_rhyme_key(sug_voc, StressDetector.detect_stress(sug_voc))
                clean_sug = strip_to_clean_letters(sug_key)
                if clean_sug and clean_target_letters:
                    if clean_sug == clean_target_letters:
                        full_rhyme.append(sug_word)
                    elif clean_sug[-1] == clean_target_letters[-1]:
                        partial_rhyme.append(sug_word)
                    else:
                        other.append(sug_word)
                else:
                    other.append(sug_word)

            # עדיפות: חרוז מלא > חרוז חלש > שאר. לפחות 5 אפשרויות
            combined = full_rhyme + partial_rhyme
            if len(combined) < 5:
                combined += other[:max(0, 5 - len(combined))]
            suggestions_per_line[line2_num] = combined if combined else other

        all_stanzas_data.append({
            "lines": lines,
            "orig_metadata": orig_metadata,
            "orig_analysis": orig_analysis,
            "expected_pairs": expected_pairs,
            "orig_alerts_by_target": orig_alerts_by_target,
            "suggestions_per_line": suggestions_per_line,
        })

    return all_stanzas_data


def render_poem_html(all_stanzas_data, suggestion_index):
    """
    מרנדר את ה-HTML לפי אינדקס ההצעה הנוכחי, ללא קריאה חוזרת ל-API.
    """
    fixed_stanzas_html = []
    has_replacements = False

    for stanza_data in all_stanzas_data:
        lines = stanza_data["lines"]
        orig_metadata = stanza_data["orig_metadata"]
        orig_analysis = stanza_data["orig_analysis"]
        expected_pairs = stanza_data["expected_pairs"]
        orig_alerts_by_target = stanza_data["orig_alerts_by_target"]
        suggestions_per_line = stanza_data["suggestions_per_line"]

        display_lines = list(lines)
        clean_lines_for_re_evaluation = list(lines)
        line_badges = {}

        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            if line2_num not in orig_alerts_by_target:
                continue
            candidates = suggestions_per_line.get(line2_num, [])
            if not candidates:
                continue
            bad_word = orig_metadata[line2_idx]["original_word"]
            final_suggestion = candidates[suggestion_index % len(candidates)]
            has_replacements = True
            line_without_last_word = lines[line2_idx].rsplit(bad_word, 1)[0]
            marked_word = f"<mark style='background-color: #ffffcc; font-weight: bold; color: #d9381e; padding: 0 4px; border-radius: 3px;'>{final_suggestion}</mark>"
            display_lines[line2_idx] = line_without_last_word + marked_word
            clean_lines_for_re_evaluation[line2_idx] = line_without_last_word + final_suggestion

        # ריצה שנייה לאימות
        new_metadata = build_lines_metadata(clean_lines_for_re_evaluation)
        new_analysis = RhymeChecker.analyze_stanza(new_metadata)
        new_alerts_by_target = {alert.get("lines", ())[1]: alert for alert in new_analysis.get("alerts", []) if len(alert.get("lines", ())) == 2}

        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            if line2_num in new_alerts_by_target:
                alert_type = new_alerts_by_target[line2_num].get("type", "חרוז חלש")
                color = "#ff9999" if alert_type == "חרוז חסר" else "#ffcc99"
                line_badges[line2_num] = f" <span style='background-color: {color}; font-size: 10px; padding: 1px 5px; border-radius: 3px; font-weight: bold; color: #333;'>⚠️ {alert_type} (צמד {line1_num}-{line2_num})</span>"
            elif clean_lines_for_re_evaluation[line2_idx] != lines[line2_idx]:
                line_badges[line2_num] = f" <span style='background-color: #b3d9ff; font-size: 10px; padding: 1px 5px; border-radius: 3px; font-weight: bold; color: #004085;'>🚀 חרוז שופר! (צמד {line1_num}-{line2_num})</span>"
            else:
                line_badges[line2_num] = f" <span style='background-color: #b3ffb3; font-size: 10px; padding: 1px 5px; border-radius: 3px; font-weight: bold; color: #1e601e;'>✨ חרוז מושלם (צמד {line1_num}-{line2_num})</span>"

        formatted_lines = [f"{display_lines[i]}{line_badges.get(i+1, '')}" for i in range(len(display_lines))]
        stanza_html = "<br>".join(formatted_lines)
        fixed_stanzas_html.append(f"<p style='margin-bottom: 25px;'>{stanza_html}</p>")

    full_html = f"<div style='direction: rtl; text-align: right; line-height: 2.0; font-size: 16px;'>{''.join(fixed_stanzas_html)}</div>"
    return full_html, has_replacements


def process_and_fix_poem_pipeline(user_poem_text, rank=0):
    """ נשמר לתאימות לאחור """
    data = analyze_poem_and_get_suggestions(user_poem_text)
    if not data:
        return "<p style='color:red;'>אנא הדביקי שיר חוקי</p>", False
    return render_poem_html(data, rank)