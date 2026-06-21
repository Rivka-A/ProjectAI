import json
import os

# נתיבי הקבצים בפרויקט שלך
INPUT_DATASET_PATH = r"C:\Users\user\ProjectAI\dataset\semi_automatic_dataset.json"
OUTPUT_TRAIN_DATA_PATH = r"C:\Users\user\ProjectAI\dataset\rhyme_training_dataset.json"

def convert_dataset_for_ai_training(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"❌ שגיאה: הקובץ {input_path} לא נמצא.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        poems = json.load(f)

    training_samples = []
    
    print(f"🔄 מתחיל לעבד {len(poems)} שירים לצורך התאמה לאימון מודל ה-AI...")

    for poem in poems:
        title = poem.get("title", "ללא כותרת")
        stanzas = poem.get("processed_stanzas", [])
        
        for stanza in stanzas:
            lines = stanza.get("lines", [])
            evaluations = stanza.get("rhyme_levels_evaluation", [])
            
            for eval_item in evaluations:
                lines_indices = eval_item.get("lines", [])
                words = eval_item.get("words", [])
                level = eval_item.get("rhyme_level")
                level_desc = eval_item.get("level_description")
                
                if len(lines_indices) < 2 or len(words) < 2:
                    continue
                
                idx1, idx2 = lines_indices[0] - 1, lines_indices[1] - 1
                
                # בניית טקסט הבית המובנה לקלט של ה-AI
                stanza_context = "\n".join([f"שורה {i+1}: {lines[i]}" for i in range(len(lines))])
                
                # אפשרות א': נמצא חרוז לא מושלם (רמות 0, 2, 3) - צריך תיקון
                if level in [0, 2, 3]:
                    prompt_input = (
                        f"משימה: תקן את החרוז בשיר.\n"
                        f"כותרת השיר: {title}\n"
                        f"הבית:\n{stanza_context}\n"
                        f"תקלה אלגוריתמית: שורה {lines_indices[1]} מסתיימת במילה '{words[1]}', "
                        f"אשר יוצרת חרוז ברמה {level} ({level_desc}) עם המילה '{words[0]}' בשורה {lines_indices[0]}.\n"
                        f"הצע מילה חלופית מנוקדת במקום '{words[1]}' שתביא לחריזה מושלמת (רמה 1) ותשמור על ההקשר הסמנטי."
                    )
                    
                    training_samples.append({
                        "input_text": prompt_input,
                        "target_word": "",  # משארים ריק - כאן יבוא התיקון האנושי/הסמנטי לצורך הלמידה
                        "is_simulated": False,
                        "original_level": level
                    })
                
                # אפשרות ב': חרוז מושלם מהמקור (רמה 1) - יוצרים דוגמת לימוד אוטומטית (Data Augmentation)
                elif level == 1:
                    # אנחנו עושים סימולציה: "מקלקלים" את הבית עבור המודל, ומציבים את המילה המקורית התקנית כ-Target
                    simulated_lines = list(lines)
                    # החלפת המילה האחרונה בשורה השנייה בצמד במילה גנרית או השמטתה לצורך אימון Masked/Generation
                    original_vocalized_word = words[1] # המילה של המשורר המקורי היא האמת הנסתרת
                    
                    prompt_input = (
                        f"משימה: השלם חרוז חסר בשיר.\n"
                        f"כותרת השיר: {title}\n"
                        f"הבית:\n{stanza_context}\n"
                        f"הנחיה: המילה האחרונה בשורה {lines_indices[1]} חסרה או דורשת שיפור. "
                        f"היא צריכה להתחרז באופן מושלם (רמה 1) עם המילה '{words[0]}' בשורה {lines_indices[0]}.\n"
                        f"מהי המילה המנוקדת המתאימה ביותר להשלמת המשמעות והחריזה?"
                    )
                    
                    training_samples.append({
                        "input_text": prompt_input,
                        "target_word": original_vocalized_word,  # המודל ילמד לייצר את המילה המקורית והטובה!
                        "is_simulated": True,
                        "original_level": level
                    })

    # שמירת קובץ האימון השטוח והמותאם
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(training_samples, f, ensure_ascii=False, indent=2)
        
    print(f"💾 קובץ האימון נוצר בהצלחה בכתובת: {output_path}")
    print(f"📊 סך הכל נוצרו {len(training_samples)} דוגמאות מוכנות לעיבוד ברשת העצבית (כולל סימולציות רמה 1).")

if __name__ == "__main__":
    convert_dataset_for_ai_training(INPUT_DATASET_PATH, OUTPUT_TRAIN_DATA_PATH)