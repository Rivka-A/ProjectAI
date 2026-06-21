import os
import json
import re

# ייבוא המחלקות הקיימות מהקבצים שלך
from .rhyme_checker import RhymeChecker
from .stress_detector import StressDetector

# הגדרת נתיבים
SOURCE_FOLDER = r"C:\Users\user\ProjectAI\target\dataset\poem_parsed_sort"
OUTPUT_DATASET_FILE = r"C:\Users\user\ProjectAI\target\dataset\semi_automatic_dataset.json"

HEBREW_DIACRITICS = re.compile(r'[\u0591-\u05C7]')

# מיפוי קבוצות עיצורים לפי מוצא הדיבור (עבור רמה 2)
PHONETIC_GROUPS = {
    'שפתיים': set('בומפ'),
    'שיניים_שורקות': set('זסשצ'),
    'חיכיות': set('גיכק'),
    'גרוניות': set('אהחע'),
    'לשוניות': set('דטלנתר')
}

def get_phonetic_group(char):
    """ מחזיר את שם קבוצת מוצא הדיבור של האות """
    for group_name, chars in PHONETIC_GROUPS.items():
        if char in chars:
            return group_name
    return None

def clean_last_word(line):
    """ 
    מנקה סימני פיסוק ומקפים מסוף השורה כדי לבודד את המילה האמיתית האחרונה בלבד.
    מטפל במקרה של מקף מפריד (-) או מקף עברי (־) בסוף השורה.
    """
    # החלפת מקפים וסימני פיסוק ברווחים, כולל מקף ארוך, מקף קצר ומקף עברי
    clean_line = re.sub(r'[.,;:?!"\'\)\(\[\-\–\—\־]', ' ', line).strip()
    words = clean_line.split()
    return words[-1] if words else ""

def prepare_line_metadata(original_line):
    """ מכין את מטא-דאטה לשורה ומזהה הטעמה """
    last_word_vocalized = clean_last_word(original_line)
    stress_type = StressDetector.detect_stress(last_word_vocalized)
    original_word_clean = HEBREW_DIACRITICS.sub('', last_word_vocalized)
    
    return {
        'original_word': original_word_clean,
        'last_word_vocalized': last_word_vocalized,
        'stress_type': stress_type
    }

def calculate_rhyme_level(key1, key2, word1_clean, word2_clean):
    """ מחשב את רמת החרוז לפי הדירוג שלכם (0-3) """
    # רמה 1: חריזה מושלמת
    if key1 == key2 and key1 != "":
        return 1, "חריזה מושלמת (סיומת שנשמעת זהה במדויק)"

    letters1 = HEBREW_DIACRITICS.sub('', key1)
    letters2 = HEBREW_DIACRITICS.sub('', key2)
    
    vowels1 = [c for c in key1 if c in ['\u05B0', '\u05B4', '\u05B5', '\u05B6', '\u05B7', '\u05B8', '\u05B9', '\u05BB', '\u05C7']]
    vowels2 = [c for c in key2 if c in ['\u05B0', '\u05B4', '\u05B5', '\u05B6', '\u05B7', '\u05B8', '\u05B9', '\u05BB', '\u05C7']]

    # רמה 2: אותו מקור עיצור
    if len(letters1) >= 2 and len(letters2) >= 2:
        if letters1[-1] == letters2[-1] and vowels1 == vowels2:
            group1 = get_phonetic_group(letters1[-2])
            group2 = get_phonetic_group(letters2[-2])
            if group1 and group2 and group1 == group2:
                return 2, f"אותו מקור עיצור (עיצורים מסוג {group1} - כמו פצוע ושסוע)"

    # רמה 3: כאשר התנועה זהה בלבד
    if vowels1 == vowels2 and len(vowels1) > 0:
        return 3, "התנועה זהה בלבד (האותיות שונות)"

    # רמה 0: לא מתחרז כלל
    return 0, "לא מתחרז כלל"

def classify_all_rhymes_v2(lines_with_metadata, line_keys, pattern_name):
    """ עוברת על הזוגות הצפויים ומסווגת אותם לפי רמות הדירוג החדשות """
    num_lines = len(line_keys)
    expected_pairs = []
    
    if num_lines == 4:
        if "א-א-א-א" in pattern_name: expected_pairs = [(0, 1), (1, 2), (2, 3)]
        elif "א-א-א" in pattern_name: expected_pairs = [(0, 1), (1, 2)]
        elif "א-א-ב-ב" in pattern_name: expected_pairs = [(0, 1), (2, 3)]
        else: expected_pairs = [(0, 2), (1, 3)]
    else:
        for i in range(num_lines - 1):
            expected_pairs.append((i, i + 1))
            
    rhyme_classifications = []
    
    for idx1, idx2 in expected_pairs:
        key1 = line_keys[idx1]
        key2 = line_keys[idx2]
        
        raw_word1 = lines_with_metadata[idx1]['original_word']
        raw_word2 = lines_with_metadata[idx2]['original_word']
        
        level_code, level_desc = calculate_rhyme_level(key1, key2, raw_word1, raw_word2)
        
        rhyme_classifications.append({
            "lines": (idx1 + 1, idx2 + 1),
            "words": (raw_word1, raw_word2),
            "rhyme_level": level_code,
            "level_description": level_desc
        })
        
    return rhyme_classifications

# --- תחילת ריצה ---
if not os.path.exists(SOURCE_FOLDER):
    print(f"❌ שגיאה: תיקיית המקור '{SOURCE_FOLDER}' לא נמצאה!")
    exit()

files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".json")]
print(f"🚀 מנתח ומסווג חרוזים לפי רמות (0-3) עם סינון מקפים עבור {len(files)} קבצים...\n")

all_analyzed_poems = []
processed_count = 0

for file_name in files:
    source_path = os.path.join(SOURCE_FOLDER, file_name)
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            poem_obj = json.load(f)
            
        stanzas = poem_obj.get("stanzas", [])
        analyzed_stanzas = []
        
        for idx, stanza in enumerate(stanzas):
            lines_with_metadata = []
            for line in stanza:
                lines_with_metadata.append(prepare_line_metadata(line))
            
            analysis_result = RhymeChecker.analyze_stanza(lines_with_metadata)
            pattern_name = analysis_result.get("pattern", "לא מזוהה")
            line_keys = analysis_result.get("line_keys", [])
            
            rhyme_details = classify_all_rhymes_v2(lines_with_metadata, line_keys, pattern_name)
            
            analyzed_stanzas.append({
                "stanza_index": idx + 1,
                "lines": stanza,
                "detected_rhyme_pattern": pattern_name,
                "rhyme_levels_evaluation": rhyme_details
            })
            
        all_analyzed_poems.append({
            "row_index": poem_obj.get("row_index"),
            "title": poem_obj.get("title"),
            "detected_genre": "poetry",
            "total_stanzas": len(stanzas),
            "processed_stanzas": analyzed_stanzas
        })
        processed_count += 1
        print(f"✓ שיר {processed_count}/{len(files)} דורג בהצלחה: '{poem_obj.get('title')}'")
    except Exception as e:
        print(f"✗ שגיאה ב-{file_name}: {e}")

print(f"\n💾 שומר את הדאטהסט המאוחד עם הדירוגים והסינון המעודכן...")
with open(OUTPUT_DATASET_FILE, "w", encoding="utf-8") as f:
    json.dump(all_analyzed_poems, f, ensure_ascii=False, indent=2)

print(f"\n=== העבודה הסתיימה! קובץ: {OUTPUT_DATASET_FILE} ===")