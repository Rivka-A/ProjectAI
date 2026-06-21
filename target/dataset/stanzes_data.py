import os
import json

SOURCE_FOLDER = "poem"
OUTPUT_FOLDER = "poem_parsed"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def parse_text_to_stanzas_balanced(text):
    raw_lines = text.split("\n")
    clean_lines = []
    
    # 1. ניקוי ופיצול לוכסנים
    for line in raw_lines:
        line_str = line.strip()
        if not line_str or "את הטקסט[ים] לעיל הפיקו" in line_str or "https://" in line_str:
            continue
        if line_str.startswith(" Hux") or (line_str.startswith("(") and line_str.endswith(")")):
            continue
            
        if "/" in line_str:
            parts = [p.strip() for p in line_str.split("/") if p.strip()]
            clean_lines.extend(parts)
        else:
            clean_lines.append(line_str)
            
    if not clean_lines:
        return "Untitled", []
        
    title = clean_lines[0]
    poem_body = clean_lines[1:]
    
    stanzas = []
    current_stanza = []
    
    # 2. חלוקה דינמית לפי סימני פיסוק (איזון השיר)
    for line in poem_body:
        current_stanza.append(line)
        
        # בדיקה במה השורה מסתיימת (מתעלמים מרווחים בסוף)
        ends_with_punctuation = line.endswith(".") or line.endswith(";") or line.endswith("!") or line.endswith("?")
        
        # תנאי סגירת בית:
        # א) זיהינו סימן פיסוק חזק המעיד על סוף בית במקור
        # ב) או שהגענו לרשת ביטחון של 6 שורות (כדי שלא יווצרו בתים ארוכים מדי)
        if ends_with_punctuation or len(current_stanza) >= 6:
            stanzas.append(current_stanza)
            current_stanza = []
            
    # הוספת השורות האחרונות שנותרו (אם ישנן)
    if current_stanza:
        stanzas.append(current_stanza)
        
    # 3. בקרת איכות: מניעת בתים "יתומים"
    # אם בטעות נוצר בית של שורה אחת בסוף, נמזג אותו לבית שלפניו כדי לשמור על המבנה
    fixed_stanzas = []
    for stanza in stanzas:
        if len(stanza) == 1 and fixed_stanzas:
            fixed_stanzas[-1].extend(stanza)
        else:
            fixed_stanzas.append(stanza)
            
    return title, fixed_stanzas

# לולאת הרצה על כל הקבצים
files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".json")]
print(f"מעבד {len(files)} קבצים מתיקיית '{SOURCE_FOLDER}' באלגוריתם פיסוק מאוזן...\n")

for file_name in files:
    source_path = os.path.join(SOURCE_FOLDER, file_name)
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            original_data = json.load(f)
            
        full_text = original_data.get("text", "")
        if not full_text and "row" in original_data:
            full_text = original_data["row"].get("text", "")
            
        if not full_text:
            continue
            
        title, stanzas = parse_text_to_stanzas_balanced(full_text)
        
        parsed_data = {
            "row_index": original_data.get("row_index", original_data.get("row_idx")),
            "title": title,
            "detected_genre": "poetry",
            "total_stanzas": len(stanzas),
            "stanzas": stanzas
        }
        
        output_path = os.path.join(OUTPUT_FOLDER, file_name)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            
        print(f"✓ {file_name} פוצל בצורה מאוזנת: '{title}' ({len(stanzas)} בתים)")
    except Exception as e:
        print(f"✗ שגיאה ב-{file_name}: {e}")

print(f"\n=== העבודה הסתיימה! הקבצים המאוזנים נשמרו בתיקייה '{OUTPUT_FOLDER}' ===")