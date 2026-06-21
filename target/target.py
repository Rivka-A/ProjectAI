# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
# from datasets import Dataset

# # 1. טעינת בסיס של מודל קוד פתוח לעברית (כדי שלא נצטרך לאמן מאפס אלפבית)
# MODEL_NAME = "Norod78/hebrew-gpt_neo-tiny" # או מודל עברית פתוח אחר
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# # 2. הכנת הנתונים מתוך ה-Dataset החצי-אוטומטי שלך
# # אנחנו יוצרים פורמט קבוע שהמודל ילמד לזהות
# def prepare_train_data(dataset_json_path):
#     # כאן את טוענת את קובץ ה-JSON שחילקת בשלבים הקודמים
#     # ומייצרת צמדים של TEXT (קלט) ו-LABEL (התיקון המצופה)
#     training_samples = []
    
#     # דוגמה למבנה טקסט שהמודל יתאמן עליו:
#     # "שיר: ... | שגיאה: שורה 3 חרוז חלש | תיקון: [המילה הנכונה]"
    
#     return Dataset.from_list(training_samples)

# # 3. הגדרות הפרמטרים של אימון ה-AI (Epochs, Learning Rate)
# training_args = TrainingArguments(
#     output_dir="./my_rhyme_ai_model",
#     num_train_epochs=5,             # כמה פעמים המודל יעבור על כל הדאטהסט
#     per_device_train_batch_size=4,  # גודל ה-Batch בהתאם לזיכרון של המחשב שלך
#     save_steps=100,
#     logging_dir="./logs",
# )

# # 4. הפעלת מנוע האימון (התהליך שבו המודל משפר את המשקולות שלו)
# trainer = Trainer(
#     model=model,
#     args=training_args,
#     train_dataset=prepare_train_data("semi_automatic_dataset.json"),
# )

# print("🏋️ מתחיל אימון של מודל ה-AI המקומי שלך...")
# trainer.train()

# # 5. שמירת המודל המאומן שלך לקובץ במערכת
# model.save_pretrained("./my_final_rhyme_ai")
# tokenizer.save_pretrained("./my_final_rhyme_ai")
# print("💾 המודל אומן בהצלחה ונשמר בתיקייה המקומית!")

import json
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from datasets import Dataset

# 1. טעינת בסיס של מודל קוד פתוח לעברית מתוך הקוד המקורי שלך
MODEL_NAME = "Norod78/hebrew-gpt_neo-tiny"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# הגדרת תו פדינג למקרה שאין למודל המקור
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 2. הכנת הנתונים מתוך ה-Dataset הקיים (semi_automatic_dataset.json)
def prepare_train_data(dataset_json_path):
    """
    טוען את קובץ ה-JSON הקיים, מוצא את הבתים שבהם נמצאו חרוזים לא מושלמים,
    ומכין אותם ישירות כדוגמאות לאימון רשת העצבית.
    """
    if not os.path.exists(dataset_json_path):
        raise FileNotFoundError(f"לא נמצא קובץ דאטהסט בנתיב: {dataset_json_path}")
        
    with open(dataset_json_path, "r", encoding="utf-8") as f:
        poems = json.load(f)
        
    training_samples = []
    
    for poem in poems:
        title = poem.get("title", "ללא כותרת")
        stanzas = poem.get("processed_stanzas", [])
        
        for stanza in stanzas:
            lines = stanza.get("lines", [])
            evaluations = stanza.get("rhyme_levels_evaluation", [])
            
            # מעבר על הניתוחים שהאלגוריתם כבר ביצע
            for eval_item in evaluations:
                level = eval_item.get("rhyme_level")
                
                # אנחנו מאמנים כרגע אך ורק על המקרים הטעונים שיפור (חרוז לא מושלם: 0, 2, 3)
                if level in [0, 2, 3]:
                    lines_indices = eval_item.get("lines", [])
                    words = eval_item.get("words", [])
                    level_desc = eval_item.get("level_description")
                    
                    if len(lines_indices) < 2 or len(words) < 2:
                        continue
                        
                    # בניית הטקסט הגולמי של הבית עבור ה-AI
                    stanza_text = "\n".join(lines)
                    
                    # יצירת פורמט טקסט קבוע שהמודל ילמד לזהות ולהשלים
                    input_prompt = (
                        f"שיר: {title}\n"
                        f"בית:\n{stanza_text}\n"
                        f"בעיה: שורות {lines_indices[0]} ו-{lines_indices[1]} לא מתחרזות מושלם (רמה {level}: {level_desc}).\n"
                        f"מילה מקורית בשורה {lines_indices[1]}: {words[1]}.\n"
                        f"הצעה לחלופה מנוקדת וסמנטית:"
                    )
                    
                    # בשלב זה, מכיוון שאין עדיין מילים מעובות ידנית, ה-Target בשלב הראשון של הריצה 
                    # הוא הניסיון של המודל ללמוד את מבנה המשפט (הטקסט המלא). 
                    # בהמשך, כשתעבה ידנית, נפריד את זה למפתח "labels" ייעודי עם המילה המתוקנת בלבד.
                    tokenized = tokenizer(
                        input_prompt,
                        truncation=True,
                        max_length=256,
                        padding="max_length"
                    )
                    
                    # הגדרת ה-Labels עבור חישוב השגיאה (Loss) של רשת העצבית
                    tokenized["labels"] = tokenized["input_ids"].copy()
                    training_samples.append(tokenized)
                    
    print(f"📊 נמצאו {len(training_samples)} בתים עם חרוזים טעוני שיפור בדאטהסט הקיים. טוען אותם לאימון...")
    return Dataset.from_list(training_samples)

# 3. הגדרות הפרמטרים של אימון ה-AI (נשאר כפי שהגדרת)
training_args = TrainingArguments(
    output_dir="./my_rhyme_ai_model",
    num_train_epochs=3,             # הורדתי ל-3 כדי שהריצה הראשונית תהיה מהירה
    per_device_train_batch_size=2,  # Batch קטן שיתאים לכל כרטיס מסך / מעבד
    save_steps=50,
    logging_dir="./logs",
    logging_steps=10
)

# 4. הפעלת מנוע האימון על בסיס הנתונים הקיימים
# עדכון הנתיב לקובץ ה-JSON המאוחד הקיים שלך במערכת
DATASET_PATH = r"C:\Users\user\ProjectAI\target\dataset\semi_automatic_dataset.json"

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=prepare_train_data(DATASET_PATH),
)

if __name__ == "__main__":
    print("🏋️ מתחיל להריץ את אימון מודל ה-AI המקומי על ה-Dataset הקיים...")
    trainer.train()
    
    # שמירת המודל בסיום הריצה
    model.save_pretrained("./my_final_rhyme_ai")
    tokenizer.save_pretrained("./my_final_rhyme_ai")
    print("💾 המודל סיים ריצה ראשונית ונשמר בתיקייה './my_final_rhyme_ai'")