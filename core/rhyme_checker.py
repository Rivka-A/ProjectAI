import re

class RhymeChecker:
    
    @staticmethod
    def normalize_vowels(text):
        """
        פונקציית עזר שמנרמלת תנועות שנשמעות זהה בעברית מודרנית
        כדי למנוע פספוס של חרוזים עקב הבדלי כתיב.
        """
        # הגדרת תווי יוניקוד של הניקוד
        qamats = '\u05B8'
        patach = '\u05B7'
        chataf_patach = '\u05B2'
        segol = '\u05B6'
        tsere = '\u05B5'
        
        # נירמול: הופכים קמץ וחטף-פתח לפתח רגיל (צליל A)
        text = text.replace(qamats, patach).replace(chataf_patach, patach)
        
        # נירמול: הופכים צירי לסגול (צליל E)
        text = text.replace(tsere, segol)
        
        return text

    @classmethod
    def extract_rhyme_key(cls, vocalized_word, stress_type):
        """
        מקבלת מילה מנוקדת וסוג הטעמה (מלעיל/מלרע),
        ומחזירה את מחרוזת מפתח החרוז המנורמל.
        """
        # 1. ניקוי סימנים מפרידים כמו קו אנכי במידה וקיים
        clean_word = vocalized_word.replace("|", "")
        
        # 2. נירמול פונטי של התנועות
        normalized_word = cls.normalize_vowels(clean_word)
        
        # הגדרת קבוצת תווי הניקוד בעברית לצורך חיפוש (טווח היוניקוד של הניקוד)
        vowel_pattern = r'[\u05B0-\u05C7]'
        
        # מציאת כל המיקומים של תנועות הניקוד במילה
        vowel_matches = list(re.finditer(vowel_pattern, normalized_word))
        
        if not vowel_matches:
            # אם אין ניקוד בכלל, נחזיר את סוף המילה כברירת מחדל
            return normalized_word[-2:]
            
        if stress_type == "מלעיל" and len(vowel_matches) >= 2:
            # במלעיל - חותכים מהתנועה הלפני-אחרונה וממשיכים עד הסוף
            target_vowel_idx = vowel_matches[-2].start()
            return normalized_word[target_vowel_idx:]
        else:
            # במלרע (או אם יש רק תנועה אחת) - חותכים מהתנועה האחרונה עד הסוף
            target_vowel_idx = vowel_matches[-1].start()
            return normalized_word[target_vowel_idx:]