import sys
import os
import requests
import re

# הוספת נתיב השורש של הפרויקט כדי שפייתון יזהה את תיקיית core
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# ייבוא המחלקות המדויקות שלך מה-Core
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector

DICTA_API_URL = "https://models.dicta.org.il/bert"

def query_dicta_bert_suggestions(stanza_lines, target_line_idx, original_word):
    """ פונה ל-API של דיקטא ומחזירה רשימת מילים מוצעות """
    masked_lines = list(stanza_lines)
    current_line = masked_lines[target_line_idx]
    
    if original_word in current_line:
        line_without_last_word = current_line.rsplit(original_word, 1)[0].strip()
    else:
        line_without_last_word = current_line.strip()
        
    masked_lines[target_line_idx] = f"{line_without_last_word} [MASK]"
    context_text = " ".join(masked_lines)
    
    payload = {"text": context_text, "top_k": 30}
    try:
        response = requests.post(DICTA_API_URL, json=payload, timeout=5)
        if response.status_code == 200:
            return [pred.get("token_str", "") for pred in response.json() 
                    if pred.get("token_str") and pred.get("token_str") not in ['.', ',', '!', '?', '[MASK]']]
    except Exception:
        pass
    return []

def build_lines_metadata(lines_list):
    """ פונקציית עזר לבניית המטא-דאטה שה-RhymeChecker שלך דורש """
    metadata = []
    for line in lines_list:
        words = line.split()
        last_word = words[-1] if words else ""
        stress_type = StressDetector.detect_stress(last_word)
        metadata.append({
            'original_word': last_word,
            'last_word_vocalized': last_word,
            'stress_type': stress_type
        })
    return metadata

def strip_html_tags(text):
    """ פונקציית עזר קריטית המנקה לחלוטין את תגי ה-HTML כדי לא להרוס את הניתוח של ה-Core """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

def process_and_fix_poem_pipeline(user_poem_text, rank=0):
    """
    המנתב המרכזי:
    מנתח צמדים, משפר בעזרת דיקטא, ומבצע בדיקה חוזרת אמינה על טקסט נקי.
    """
    if not user_poem_text.strip():
        return "<p style='color:red;'>אנא הדביקי שיר חוקי</p>", False

    raw_stanzas = user_poem_text.split("\n\n")
    fixed_stanzas_html = []
    has_replacements = False
    
    for stanza_idx, raw_stanza in enumerate(raw_stanzas):
        lines = [line.strip() for line in raw_stanza.split("\n") if line.strip()]
        if not lines:
            continue
            
        num_lines = len(lines)
        display_lines = list(lines)
        clean_lines_for_re_evaluation = list(lines) # ישמור את הגרסה הנקייה לריצה השנייה
        line_badges = {}
        
        # 1. ריצה ראשונה: ניתוח המצב המקורי של הבית
        orig_metadata = build_lines_metadata(lines)
        orig_analysis = RhymeChecker.analyze_stanza(orig_metadata)
        orig_alerts = orig_analysis.get("alerts", [])
        
        orig_alerts_by_target = {alert.get("lines", ())[1]: alert for alert in orig_alerts if len(alert.get("lines", ())) == 2}
        
        # קביעת הצמדים שנבדקים
        expected_pairs = []
        if num_lines == 4:
            pattern = orig_analysis.get("pattern", "")
            if "א-ב-א-ב" in pattern: expected_pairs = [(1, 3), (2, 4)]
            elif "א-ב-ב-א" in pattern: expected_pairs = [(1, 4), (2, 3)]
            else: expected_pairs = [(1, 2), (3, 4)]
        else:
            for i in range(1, num_lines): expected_pairs.append((i, i + 1))

        # 2. שלב השיפור בעזרת דיקטא
        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            
            if line2_num in orig_alerts_by_target:
                bad_word = orig_metadata[line2_idx]["original_word"]
                suggestions = query_dicta_bert_suggestions(lines, line2_idx, bad_word)
                valid_rhyme_suggestions = []
                key_to_match = orig_analysis["line_keys"][line1_num - 1]
                
                for sug_word in suggestions:
                    sug_stress = StressDetector.detect_stress(sug_word)
                    sug_key = RhymeChecker.extract_rhyme_key(sug_word, sug_stress)
                    if sug_key == key_to_match:
                        valid_rhyme_suggestions.append(sug_word)
                
                final_suggestion = None
                if valid_rhyme_suggestions:
                    final_suggestion = valid_rhyme_suggestions[rank % len(valid_rhyme_suggestions)]
                elif suggestions:
                    final_suggestion = suggestions[rank % len(suggestions)]
                
                if final_suggestion and final_suggestion != bad_word:
                    has_replacements = True
                    orig_line = lines[line2_idx]
                    line_without_last_word = orig_line.rsplit(bad_word, 1)[0]
                    
                    # גרסה לתצוגה ויזואלית (עם HTML)
                    marked_word = f"<mark style='background-color: #ffffcc; font-weight: bold; color: #d9381e; padding: 0 4px; border-radius: 3px;'>{final_suggestion}</mark>"
                    display_lines[line2_idx] = line_without_last_word + marked_word
                    
                    # גרסה נקייה לחלוטין לטובת ה-Core (בלי שום HTML)
                    clean_lines_for_re_evaluation[line2_idx] = line_without_last_word + final_suggestion

        # 3. ריצה שנייה: ניתוח המצב החדש על בסיס הטקסט הנקי המשופר
        new_metadata = build_lines_metadata(clean_lines_for_re_evaluation)
        new_analysis = RhymeChecker.analyze_stanza(new_metadata)
        new_alerts = new_analysis.get("alerts", [])
        new_alerts_by_target = {alert.get("lines", ())[1]: alert for alert in new_alerts if len(alert.get("lines", ())) == 2}

        # 4. הדבקת תגים מעודכנים דינמית בסופי צמדים
        for line1_num, line2_num in expected_pairs:
            line2_idx = line2_num - 1
            
            # אם השורה עדיין מייצרת שגיאה בריצה השנייה
            if line2_num in new_alerts_by_target:
                current_alert = new_alerts_by_target[line2_num]
                alert_type = current_alert.get("type", "חרוז חלש")
                color = "#ff9999" if alert_type == "חרוז חסר" else "#ffcc99"
                line_badges[line2_num] = f" <span style='background-color: {color}; font-size: 10px; padding: 1px 5px; border-radius: 3px; font-weight: bold; color: #333;'>⚠️ {alert_type} (צמד {line1_num}-{line2_num})</span>"
            else:
                # אם הכל תקין עכשיו - נבדוק אם זה בזכות השינוי או שהיה ככה תמיד
                if clean_lines_for_re_evaluation[line2_idx] != lines[line2_idx]:
                    line_badges[line2_num] = f" <span style='background-color: #b3d9ff; font-size: 10px; padding: 1px 5px; border-radius: 3px; font-weight: bold; color: #004085;'>🚀 חרוז שופר! (צמד {line1_num}-{line2_num})</span>"
                else:
                    line_badges[line2_num] = f" <span style='background-color: #b3ffb3; font-size: 10px; padding: 1px 5px; border-radius: 3px; font-weight: bold; color: #1e601e;'>✨ חרוז מושלם (צמד {line1_num}-{line2_num})</span>"

        # 5. הרכבת ה-HTML
        formatted_lines = []
        for i, idx_line in enumerate(display_lines):
            line_num = i + 1
            badge = line_badges.get(line_num, "")
            formatted_lines.append(f"{idx_line}{badge}")
            
        stanza_html = "<br>".join(formatted_lines)
        fixed_stanzas_html.append(f"<p style='margin-bottom: 25px;'>{stanza_html}</p>")
        
    full_html_output = f"<div style='direction: rtl; text-align: right; line-height: 2.0; font-size: 16px;'>{''.join(fixed_stanzas_html)}</div>"
    return full_html_output, has_replacements