import json
import requests

# נקרא 20 שורות לדוגמה כדי לבדוק ולסנן (ניתן לשנות את ה-limit וה-offset לפי הצורך)
DATASET_API_URL = "https://datasets-server.huggingface.co/rows?dataset=NHLOCAL/project-ben-yehuda&config=default&split=train&offset=270&limit=20"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def is_poetry(text):
    """
    פונקציה הבודקת האם הטקסט הוא שיר לפי מבנה השורות שלו.
    """
    if not text or not text.strip():
        return False
        
    # פירוק הטקסט לשורות ונקיון רווחים
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    if len(lines) < 3:
        return False  # קצר מדי מכדי לאבחן כמבנה של שיר
        
    # חישוב אורך ממוצע של מילים בשורה
    total_words = sum(len(line.split()) for line in lines)
    average_words_per_line = total_words / len(lines)
    
    # בשירה העברית הקלאסית שורה ממוצעת קצרה משמעותית מפסקה (לרוב פחות מ-7-8 מילים)
    return average_words_per_line < 8

try:
    print("מושך נתונים ומבצע סינון קבצים (שמירת שירים בלבד)...")
    response = requests.get(DATASET_API_URL, headers=headers, timeout=20)
    response.raise_for_status()
    
    data = response.json()
    rows = data.get("rows", [])
    
    saved_count = 0
    
    for row_item in rows:
        row_id = row_item.get("row_idx")
        full_text = row_item.get("row", {}).get("text", "")
        
        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
        title_preview = lines[0][:30] + "..." if lines else f"Row {row_id}"
        
        # הרצת הבדיקה: אם זה לא שיר -> מדלגים על השורה הזו ולא שומרים קובץ!
        if not is_poetry(full_text):
            print(f"⏩ שורה {row_id} דולגה (זוהה כפרוזה/מאמר): {title_preview}")
            continue  # עובר מיד לשורה הבאה בלולאה ללא כתיבת קובץ
            
        # הגענו לכאן? סימן שהטקסט עבר את הסינון והוא אכן שיר
        print(f"🎵 שורה {row_id} זוהתה כשיר! מייצר קובץ...")
        
        poem_data = {
            "row_index": row_id,
            "detected_genre": "poetry",
            "text": full_text
        }
        
        file_name = f"./poem/poem_row_{row_id}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(poem_data, f, ensure_ascii=False, indent=2)
            
        saved_count += 1

    print(f"\nהסתיים בהצלחה! נשמרו {saved_count} שירים מתוך {len(rows)} שורות שנבדקו.")

except Exception as e:
    print(f"✗ שגיאה: {e}")