# import re

# class RhymeChecker:
#     @staticmethod
#     def normalize_hebrew_vowels(vocalized_word):
#         """
#         פונקציית עזר שמנרמלת תנועות זהות פונטית בעברית מודרנית
#         ומסירה סימנים שאינם משפיעים על צליל החרוז (כמו דגש).
#         """
#         # הגדרת תווי יוניקוד
#         sheva = '\u05B0'
#         hatef_segol = '\u05B1'
#         hatef_patah = '\u05B2'
#         hatef_qamats = '\u05B3'
#         hiriq = '\u05B4'
#         tsere = '\u05B5'
#         segol = '\u05B6'
#         patah = '\u05B7'
#         qamats = '\u05B8'
#         holam = '\u05B9'
#         qumuts = '\u05BB'
#         dagesh = '\u05BC'  # תו היוניקוד של נקודת הדגש/מפיק פנימי
        
#         normalized = vocalized_word
        
#         # 1. ניקוי סימנים מפריעים
#         normalized = normalized.replace("|", "")
#         normalized = normalized.replace(dagesh, "")  # הסרת הדגש מהמילה
        
#         # 2. נרמול תנועות זהות פונטית
#         normalized = normalized.replace(hatef_patah, patah)
#         normalized = normalized.replace(hatef_segol, segol)
#         normalized = normalized.replace(qamats, patah)
#         normalized = normalized.replace(tsere, segol)
#         normalized = normalized.replace(hatef_qamats, holam)
        
#         return normalized

#     @classmethod
#     def extract_rhyme_key(cls, vocalized_word, stress_type):
#         """
#         הפונקציה המרכזית המעודכנת: מחלצת את מפתח החרוז המדויק.
#         """
#         # 1. נרמול התנועות במילה
#         clean_word = cls.normalize_hebrew_vowels(vocalized_word)
        
#         # רשימת כל סימני הניקוד (התנועות) בעברית
#         vowels = [
#             '\u05B0', '\u05B4', '\u05B5', '\u05B6', 
#             '\u05B7', '\u05B8', '\u05B9', '\u05BB',
#             '\u05C7'
#         ]
        
#         # מציאת המיקומים של כל התנועות במילה
#         vowel_indices = [i for i, char in enumerate(clean_word) if char in vowels]
        
#         if not vowel_indices:
#             return clean_word[-2:]
            
#         if stress_type == "מלרע":
#             # מלרע: החרוז מתחיל מהתנועה האחרונה.
#             # נחתוך בדיוק ממיקום התנועה האחרונה
#             last_vowel_idx = vowel_indices[-1]
#             return clean_word[last_vowel_idx:]
            
#         elif stress_type == "מלעיל":
#             # מלעיל: החרוז מתחיל מהתנועה הלפני-אחרונה.
#             if len(vowel_indices) >= 2:
#                 target_vowel_idx = vowel_indices[-2]
#             else:
#                 target_vowel_idx = vowel_indices[0]
            
#             # חותכים בדיוק מהתנועה המוטעמת הלפני-אחרונה ועד סוף המילה
#             return clean_word[target_vowel_idx:]
            
#         return clean_word
    
#     @classmethod
#     def analyze_stanza(cls, lines_with_metadata):
#         """
#         פונקציה המקבלת רשימה של שורות הבית, כאשר לכל שורה יש את:
#         הטקסט המקורי, המילה האחרונה המנוקדת, וסוג ההטעמה שלה.
#         היא מזהה את תבנית החריזה ומחזירה דוח התרעות.
#         """
#         # 1. חילוץ מפתחות החרוז לכל השורות בבית
#         line_keys = []
#         for line in lines_with_metadata:
#             vocalized_word = line['last_word_vocalized']
#             stress_type = line['stress_type']
#             rhyme_key = cls.extract_rhyme_key(vocalized_word, stress_type)
#             line_keys.append(rhyme_key)
            
#         num_lines = len(line_keys)
#         if num_lines < 2:
#             return {"pattern": "לא מוגדר", "alerts": ["הבית קצר מדי מכדי לנתח חריזה"]}

#         # 2. זיהוי אוטומטי של תבנית החריזה (עבור בתים של 4 שורות)
#         # נבדוק שתי תבניות נפוצות: א-א-ב-ב או א-ב-א-ב
#         pattern_name = "לא מזוהה"
#         expected_pairs = [] # הזוגות שאמורים להתחרז לפי התבנית
        
#         if num_lines == 4:
#             # בדיקת התאמה לתבנית א-א-ב-ב (שורה 1 עם 2, שורה 3 עם 4)
#             score_aabb = (1 if line_keys[0] == line_keys[1] else 0) + (1 if line_keys[2] == line_keys[3] else 0)
#             # בדיקת התאמה לתבנית א-ב-א-ב (שורה 1 עם 3, שורה 2 עם 4)
#             score_abba=(1 if line_keys[0]==line_keys[3] else 0) + (1 if line_keys[1]==line_keys[2] else 0)
#             score_abab = (1 if line_keys[0] == line_keys[2] else 0) + (1 if line_keys[1] == line_keys[3] else 0)
#             score_aaa= (1 if line_keys[0] == line_keys[1] == line_keys[2] else 0) + (1 if line_keys[0]== line_keys[1] == line_keys[2] == line_keys[3] else 0)

#             if score_aaa == 1:
#                 pattern_name = "א-א-א (חריזה פיוטית)"
#                 expected_pairs = [(0, 1), (1, 2)]
#             elif score_aaa == 2:
#                 pattern_name = "א-א-א-א (חריזה מושלמת)"
#                 expected_pairs = [(0, 1), (2, 3)]
#             elif score_aabb >= score_abab:
#                 pattern_name = "א-א-ב-ב (חריזה צמודה)"
#                 expected_pairs = [(0, 1), (2, 3)]
#             elif score_abab ==2:
#                 pattern_name = "א-ב-א-ב (חריזה מסורגת)"
#                 expected_pairs = [(0, 2), (1, 3)]
#             else:
#                 pattern_name = "א-ב-א-ב (חריזה מסורגת)"
#                 expected_pairs = [(0, 1), (2, 3)] # נגדיר את הציפייה לפי המיקומים (0 עם 2, 1 עם 3)
#                 expected_pairs = [(0, 2), (1, 3)]
#         else:
#             pattern_name = "חריזה חופשית / אחר"
#             for i in range(num_lines - 1):
#                 expected_pairs.append((i, i + 1))

#         # 3. מנגנון הפקת התרעות (חיפוש חרוזים חסרים או חלשים)
#         alerts = []
#         for idx1, idx2 in expected_pairs:
#             key1 = line_keys[idx1]
#             key2 = line_keys[idx2]
            
#             # אם המפתחות זהים לחלוטין - החרוז מושלם!
#             if key1 == key2:
#                 continue
                
#             # הגדרת "חרוז חלש": האותיות האחרונות זהות, אך התנועה המוטעמת שונה
#             # (למשל: סוּס ו-מָטוֹס מסתיימים שניהם באות ס', אך התנועה שונה)
#             raw_word1 = lines_with_metadata[idx1]['original_word']
#             raw_word2 = lines_with_metadata[idx2]['original_word']
            
#             if key1[-1] == key2[-1]:
#                 alerts.append({
#                     "type": "חרוז חלש",
#                     "lines": (idx1 + 1, idx2 + 1),
#                     "message": f"שורה {idx1 + 1} ({raw_word1}) ושורה {idx2 + 1} ({raw_word2}) מסתיימות באות זהה אך התנועות שונות (חרוז חלש)."
#                 })
#             else:
#                 # חרוז חסר לחלוטין - המפתחות שונים לגמרי במקום שבו התבנית מכתיבה חריזה
#                 alerts.append({
#                     "type": "חרוז חסר",
#                     "lines": (idx1 + 1, idx2 + 1),
#                     "message": f"לפי תבנית {pattern_name}, שורה {idx1 + 1} ({raw_word1}) ושורה {idx2 + 1} ({raw_word2}) אמורות להתחרז, אך אין ביניהן חריזה."
#                 })

#         return {
#             "pattern": pattern_name,
#             "alerts": alerts,
#             "line_keys": line_keys
#         }

import re

class RhymeChecker:
    @staticmethod
    def normalize_hebrew_vowels(vocalized_word):
        """
        פונקציית עזר שמנרמלת תנועות זהות פונטית בעברית מודרנית
        ומסירה סימנים שאינם משפיעים על צליל החרוז (כמו דגש).
        """
        sheva = '\u05B0'
        hatef_segol = '\u05B1'
        hatef_patah = '\u05B2'
        hatef_qamats = '\u05B3'
        hiriq = '\u05B4'
        tsere = '\u05B5'
        segol = '\u05B6'
        patah = '\u05B7'
        qamats = '\u05B8'
        holam = '\u05B9'
        qumuts = '\u05BB'
        dagesh = '\u05BC'
        
        normalized = vocalized_word
        
        # 1. ניקוי סימנים מפריעים
        normalized = normalized.replace("|", "")
        normalized = normalized.replace(dagesh, "")
        
        # 2. נרמול תנועות זהות פונטית
        normalized = normalized.replace(hatef_patah, patah)
        normalized = normalized.replace(hatef_segol, segol)
        normalized = normalized.replace(qamats, patah)
        normalized = normalized.replace(tsere, segol)
        normalized = normalized.replace(hatef_qamats, holam)
        
        return normalized

    @staticmethod
    def apply_phonetic_replacements(vocalized_text):
        """
        הפונקציה הקריטית: מחליפה רק את העיצורים הגולמיים שנשמעות זהה,
        בלי לפגוע או למחוק את סימני הניקוד הצמודים אליהם!
        """
        # מילון החלפות של אותיות עיצוריות בלבד
        phonetic_map = {
            'ט': 'ת',  # מִבְטָח -> מִבְתָּח
            'כ': 'ח',  # כ' רפה ו-ח' 
            'ק': 'כ',  # ק' ו-כ' דגושה
            'ס': 'ש',  # ס' ו-ש' שמאלית
            'א': 'ע',
        }
        
        result = []
        for char in vocalized_text:
            # אם התו הוא אות עיצורית שנמצאת במילון, נחליף אותה ונשמור על הניקוד שאחריה
            if char in phonetic_map:
                result.append(phonetic_map[char])
            else:
                result.append(char)
                
        return "".join(result)

    @classmethod
    def extract_rhyme_key(cls, vocalized_word, stress_type):
        """
        מחלץ את מפתח החרוז המדויק על בסיס מיקום ההטעמה,
        תוך שמירה מלאה על הניקוד המקורי ונרמול פונטי ממוקד.
        """
        # 1. נרמול תנועות בסיסי (קמץ לפתח וכו')
        clean_word = cls.normalize_hebrew_vowels(vocalized_word)
        
        # רשימת תווי הניקוד בעברית
        vowels = [
            '\u05B0', '\u05B4', '\u05B5', '\u05B6', 
            '\u05B7', '\u05B8', '\u05B9', '\u05BB',
            '\u05C7'
        ]
        
        vowel_indices = [i for i, char in enumerate(clean_word) if char in vowels]
        
        if not vowel_indices:
            # אם אין ניקוד בכלל, נחזיר את 2 האותיות האחרונות כברירת מחדל
            return cls.apply_phonetic_replacements(clean_word[-2:])
            
        # 2. חיתוך אזור החרוז בהתאם למיקום ההטעמה
        if stress_type == "מלרע":
            # מלרע: החרוז מתחיל מהתנועה האחרונה במילה
            last_vowel_idx = vowel_indices[-1]
            rhyme_zone = clean_word[last_vowel_idx:]
        else:
            # מלעיל: החרוז מתחיל מהתנועה הלפני-אחרונה
            if len(vowel_indices) >= 2:
                target_vowel_idx = vowel_indices[-2]
            else:
                target_vowel_idx = vowel_indices[0]
            rhyme_zone = clean_word[target_vowel_idx:]
            
        # 3. החלת ההחלפה הפונטית על אזור החרוז המנוקד
        # "בְטָח" יהפוך ל-"בְתָח" | "תָּח" יישאר "תָּח" -> שניהם יסתיימו ב-"תָח" מנוקד לחלוטין!
        final_key = cls.apply_phonetic_replacements(rhyme_zone)
        return final_key
    
    @classmethod
    def analyze_stanza(cls, lines_with_metadata):
        """
        מזהה את תבנית החריזה ומפיקה דוח התרעות מדויק.
        """
        line_keys = []
        for line in lines_with_metadata:
            vocalized_word = line['last_word_vocalized']
            stress_type = line['stress_type']
            rhyme_key = cls.extract_rhyme_key(vocalized_word, stress_type)
            line_keys.append(rhyme_key)
            
        num_lines = len(line_keys)
        if num_lines < 2:
            return {"pattern": "לא מוגדר", "alerts": ["הבית קצר מדי מכדי לנתח חריזה"]}

        pattern_name = "לא מזוהה"
        expected_pairs = []
        
        if num_lines == 4:
            score_aabb = (1 if line_keys[0] == line_keys[1] else 0) + (1 if line_keys[2] == line_keys[3] else 0)
            score_abab = (1 if line_keys[0] == line_keys[2] else 0) + (1 if line_keys[1] == line_keys[3] else 0)
            score_abba = (1 if line_keys[0] == line_keys[3] else 0) + (1 if line_keys[1] == line_keys[2] else 0)
            
            is_aaaa = (line_keys[0] == line_keys[1] == line_keys[2] == line_keys[3])
            is_aaab = (line_keys[0] == line_keys[1] == line_keys[2]) and (line_keys[2] != line_keys[3])

            if is_aaaa:
                pattern_name = "א-א-א-א (חריזה מלאה)"
                expected_pairs = [(0, 1), (1, 2), (2, 3)]
            elif is_aaab:
                pattern_name = "א-א-א-ב (חריזה פיוטית)"
                expected_pairs = [(0, 1), (1, 2)]
            elif score_abab >= 1 and score_abab >= score_aabb and score_abab >= score_abba:
                pattern_name = "א-ב-א-ב (חריזה מסורגת)"
                expected_pairs = [(0, 2), (1, 3)]
            elif score_abba >= 1 and score_abba >= score_aabb and score_abba >= score_abab:
                pattern_name = "א-ב-ב-א (חריזה חובקת)"
                expected_pairs = [(0, 3), (1, 2)]
            else:
                pattern_name = "א-א-ב-ב (חריזה צמודה)"
                expected_pairs = [(0, 1), (2, 3)]
        else:
            pattern_name = "חריזה חופשית / אחר"
            for i in range(num_lines - 1):
                expected_pairs.append((i, i + 1))

        alerts = []
        for idx1, idx2 in expected_pairs:
            key1 = line_keys[idx1]
            key2 = line_keys[idx2]
            
            if key1 == key2:
                continue
                
            raw_word1 = lines_with_metadata[idx1]['original_word']
            raw_word2 = lines_with_metadata[idx2]['original_word']
            
            # ניקוי הניקוד רק לצורך בדיקת ה"חרוז החלש" (אות אחרונה זהה פונטית)
            clean_letters1 = "".join([c for c in key1 if '\u05D0' <= c <= '\u05EA'])
            clean_letters2 = "".join([c for c in key2 if '\u05D0' <= c <= '\u05EA'])
            
            if clean_letters1 and clean_letters2 and clean_letters1[-1] == clean_letters2[-1]:
                alerts.append({
                    "type": "חרוז חלש",
                    "lines": (idx1 + 1, idx2 + 1),
                    "message": f"שורה {idx1 + 1} ({raw_word1}) ושורה {idx2 + 1} ({raw_word2}) מסתיימות בצליל עיצורי זהה אך התנועות שונות."
                })
            else:
                alerts.append({
                    "type": "חרוז חסר",
                    "lines": (idx1 + 1, idx2 + 1),
                    "message": f"לפי תבנית {pattern_name}, שורה {idx1 + 1} ({raw_word1}) ושורה {idx2 + 1} ({raw_word2}) אמורות להתחרז, אך אין ביניהן חריזה."
                })

        return {
            "pattern": pattern_name,
            "alerts": alerts,
            "line_keys": line_keys
        }