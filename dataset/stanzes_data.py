import os
import json

# הגדרת תיקיות המקור והיעד
SOURCE_FOLDER = "poem"
OUTPUT_FOLDER = "poem_parsed"

# יצירת תיקיית היעד אם היא אינה קיימת
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    print(f"📁 התיקייה '{OUTPUT_FOLDER}' נוצרה בהצלחה.")

# וידוי שתיקיית המקור קיימת
if not os.path.exists(SOURCE_FOLDER):
    print(f"❌ שגיאה: תיקיית המקור '{SOURCE_FOLDER}' לא נמצאה! אנא ודא שהתיקייה קיימת ומכילה קבצים.")
    exit()

def parse_text_to_stanzas(text):
    """ מנקה את הטקסט ומפצל אותו לבתים בצורה חכמה לפי סימני פיסוק ואורך שורה """
    all_lines = [line.strip() for line in text.split("\n")]
    
    clean_lines = []
    for line in all_lines:
        # סינון שורות ריקות וסינון קרדיטים של פרויקט בן יהודה בסוף
        if not line or "את הטקסט[ים] לעיל הפיקו" in line or "https://" in line:
            continue
        # סינון הערות שוליים בסוגריים (כמו אסף ל"ז נ')
        if line.startswith("(") and line.endswith(")"):
            continue
        clean_lines.append(line)
        
    if not clean_lines:
        return "Untitled", []

    # השורה הראשונה מוגדרת ככותרת, השאר הם גוף השיר
    title = clean_lines[0]
    poem_body_lines = clean_lines[1:]
    
    stanzas = []
    current_stanza = []
    
    # חלוקה לבתים לפי נקודות בסוף משפט או הגעה ל-6 שורות
    for line in poem_body_lines:
        current_stanza.append(line)
        
        # תנאי סגירת בית: סוף משפט (נקודה/סימן קריאה) או בית שהגיע ל-6 שורות
        if line.endswith(".") or line.endswith("!") or line.endswith("?") or len(current_stanza) >= 6:
            stanzas.append(current_stanza)
            current_stanza = []
            
    # אם נשארו שורות בסוף, נכניס אותן כבית האחרון
    if current_stanza:
        stanzas.append(current_stanza)
        
    return title, stanzas

# קריאת כל קבצי ה-JSON מתיקיית המקור
files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".json")]
print(f"מזהה {len(files)} קבצים בתיקיית '{SOURCE_FOLDER}'... מתחיל בעיבוד...\n")

processed_count = 0

for file_name in files:
    source_path = os.path.join(SOURCE_FOLDER, file_name)
    
    try:
        # 1. קריאת קובץ המקור
        with open(source_path, "r", encoding="utf-8") as f:
            original_data = json.load(f)
            
        # חילוץ הטקסט הגולמי (תומך גם אם המפתח הוא 'text' וגם אם המבנה פנימי)
        full_text = original_data.get("text", "")
        if not full_text and "row" in original_data:
            full_text = original_data["row"].get("text", "")
            
        if not full_text:
            print(f"⏩ מדלג על {file_name} - לא נמצא טקסט בפנים.")
            continue
            
        # 2. הרצת פונקציית החלוקה החכמה לבתים
        title, stanzas = parse_text_to_stanzas(full_text)
        
        # 3. בניית מבנה ה-JSON החדש והנקי
        parsed_data = {
            "row_index": original_data.get("row_index", original_data.get("row_idx")),
            "title": title,
            "detected_genre": "poetry",
            "total_stanzas": len(stanzas),
            "stanzas": stanzas
        }
        
        # 4. שמירה בתיקיית היעד החדשה
        output_path = os.path.join(OUTPUT_FOLDER, file_name)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            
        processed_count += 1
        print(f"✓ {file_name} פוצל בהצלחה: '{title}' ({len(stanzas)} בתים)")

    except Exception as e:
        print(f"✗ שגיאה בעיבוד הקובץ {file_name}: {e}")

print(f"\n=== הסתיים! {processed_count} קבצים פוצלו לבתים ונשמרו בתיקייה '{OUTPUT_FOLDER}'. ===")