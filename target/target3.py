import json
import os
import requests

# נתיב קובץ ה-JSON הקיים שלך
DATASET_PATH = r"C:\Users\user\ProjectAI\target\dataset\semi_automatic_dataset.json"

# כתובת ה-API הרשמית והפתוחה של דיקטא למודל השפה (DictaBERT)
DICTA_API_URL = "https://models.dicta.org.il/bert"

def query_dicta_bert_api(stanza_lines, target_line_idx, original_word):
    """
    פונקציה הפונה ל-API של דיקטא.
    היא מחליפה את המילה האחרונה בשורה הבעייתית בתו [MASK],
    ומבקשת מהמודל של דיקטא לנחש חלופות מתאימות סמנטית.
    """
    # יצירת עותק של השורות כדי לא להרוס את המקור
    masked_lines = list(stanza_lines)
    
    # ניקוי השורה הבעייתית והחלפת המילה האחרונה ב-[MASK]
    current_line = masked_lines[target_line_idx]
    # הסרת המילה המקורית מסוף השורה והחלפתה ב-[MASK]
    line_without_last_word = current_line.rsplit(original_word, 1)[0].strip()
    masked_lines[target_line_idx] = f"{line_without_last_word} [MASK]"
    
    # חיבור הבית כולו לטקסט רציף אחד עבור ה-API
    context_text = " ".join(masked_lines)
    
    # הכנת הנתונים (Payload) בפורמט שדיקטא דורשים
    payload = {
        "text": context_text,
        "top_k": 5  # נבקש את 5 ההצעות הסמנטיות המובילות
    }
    
    try:
        # ביצוע קריאת ה-API (פתוח בנטפרי)
        response = requests.post(DICTA_API_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            predictions = response.json()
            suggestions = []
            
            # חילוץ המילים המוצעות מתוך התשובה של דיקטא
            for pred in predictions:
                token_str = pred.get("token_str", "")
                score = pred.get("score", 0)
                
                # נסנן סימני פיסוק או תווים ריקים שהמודל עלול להציע
                if token_str and token_str not in ['.', ',', '!', '?', '[MASK]']:
                    suggestions.append({
                        "word": token_str,
                        "confidence_score": round(score * 100, 2)
                    })
            return suggestions
        else:
            print(f"⚠️ שגיאה בפנייה לדיקטא (קוד שגיאה {response.status_code})")
            return []
            
    except Exception as e:
        print(f"❌ שגיאת תקשורת עם ה-API של דיקטא: {e}")
        return []

def run_rhyme_ai_assistant(dataset_json_path):
    """
    הפונקציה המרכזית שעוברת על ה-Dataset הקיים, מוצאת חרוזים חלשים,
    ופונה בזמן אמת ל-API של דיקטא כדי להביא חלופות סמנטיות.
    """
    if not os.path.exists(dataset_json_path):
        raise FileNotFoundError(f"לא נמצא קובץ דאטהסט בנתיב: {dataset_json_path}")
        
    with open(dataset_json_path, "r", encoding="utf-8") as f:
        poems = json.load(f)
        
    print(f"🚀 מפעיל עוזר חריזה מבוסס API דיקטא על הדאטהסט הקיים...")
    
    # מעבר על השירים והבתים
    for poem in poems:
        title = poem.get("title", "ללא כותרת")
        stanzas = poem.get("processed_stanzas", [])
        
        for idx, stanza in enumerate(stanzas):
            lines = stanza.get("lines", [])
            evaluations = stanza.get("rhyme_levels_evaluation", [])
            
            for eval_item in evaluations:
                level = eval_item.get("rhyme_level")
                
                # אם מצאנו חרוז טעון שיפור (רמות 0, 2, 3)
                if level in [0, 2, 3]:
                    lines_indices = eval_item.get("lines", [])
                    words = eval_item.get("words", [])
                    
                    if len(lines_indices) < 2 or len(words) < 2:
                        continue
                    
                    # השורה השנייה בצמד היא זו שנרצה להציע לה חלופות
                    target_line_num = lines_indices[1]
                    target_line_idx = target_line_num - 1
                    bad_word = words[1]
                    
                    print(f"\n💡 נמצא חרוז טעון שיפור בשיר '{title}' (בית {idx+1}):")
                    print(f"   המילים '{words[0]}' ו-'{bad_word}' פגומות ברמה {level}.")
                    print(f"   🔄 פונה ל-API של דיקטא לקבלת חלופות סמנטיות לשורה {target_line_num}...")
                    
                    # פנייה לדיקטא
                    ai_suggestions = query_dicta_bert_api(lines, target_line_idx, bad_word)
                    
                    # הצגת התוצאות על המסך בזמן אמת
                    if ai_suggestions:
                        print("   ✨ הצעות סמנטיות מה-AI של דיקטא:")
                        for sug in ai_suggestions:
                            print(f"      - המילה: '{sug['word']}' (התאמה סמנטית: {sug['confidence_score']}%)")
                        
                        # הוספת ההצעות ישירות לתוך מבנה הנתונים הקיים
                        eval_item["dicta_ai_suggestions"] = ai_suggestions
                    else:
                        print("   ❌ לא התקבלו הצעות מה-AI.")
                        eval_item["dicta_ai_suggestions"] = []

    # שמירה חזרה של הקובץ המעודכן עם ההצעות בפנים
    output_path = dataset_json_path.replace(".json", "_with_dicta.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(poems, f, ensure_ascii=False, indent=2)
        
    print(f"\n💾 התהליך הסתיים! הקובץ המועשר עם הצעות ה-AI נשמר ב: {output_path}")

if __name__ == "__main__":
    run_rhyme_ai_assistant(DATASET_PATH)