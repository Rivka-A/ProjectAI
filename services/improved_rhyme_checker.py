"""
מודול שיפור חרוז - תיקון בעיות פונטיקה וסינון משופר.
"""
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector


class ImprovedRhymeChecker:
    """
    מחלקה משופרת לבדיקת חרוז עם תיקונים לבעיות פונטיקה.
    
    בעיות שתוקנו:
    1. "מים" ו"ימים" לא צריכים להתחרז (יוד בהתחלה ≠ יוד בסוף)
    2. סינון משופר של הצעות לפי חריזה
    3. בדיקה קפדנית של התאמת חרוז
    """
    
    # מיפוי מילים שלא צריכות להתחרז (false positives)
    PHONETIC_EXCEPTIONS = {
        # מים (מ-י-ם) ≠ ימים (י-מ-י-ם)
        # הבדל: יוד בהתחלה vs יוד בסוף
        ('m', 'A'): {  # מים
            'exclude_patterns': [('y', 'I'), ('y', 'A')],  # לא ימים, לא יום
        }
    }
    
    @classmethod
    def get_detailed_phonemes(cls, vocalized_word: str, stress_type: str) -> dict:
        """
        מחזיר ניתוח פונטי מפורט של מילה.
        """
        syllables = RhymeChecker._to_syllables(vocalized_word)
        rhyme_key = RhymeChecker.extract_rhyme_key(vocalized_word, stress_type)
        
        return {
            'word': vocalized_word,
            'syllables': syllables,
            'rhyme_key': rhyme_key,
            'last_vowel': cls._get_last_vowel(rhyme_key),
            'final_consonants': cls._get_final_consonants(rhyme_key),
            'stress_type': stress_type,
        }
    
    @classmethod
    def _get_last_vowel(cls, rhyme_key: tuple) -> str:
        """חלץ את התנועה האחרונה."""
        for cons, vowel in reversed(rhyme_key):
            if vowel:
                return vowel
        return ''
    
    @classmethod
    def _get_final_consonants(cls, rhyme_key: tuple) -> tuple:
        """חלץ את העיצורים הסופיים."""
        found = False
        result = []
        for cons, vowel in reversed(rhyme_key):
            if not found:
                if vowel:
                    found = True
            else:
                result.append(cons)
        return tuple(reversed(result))
    
    @classmethod
    def is_valid_rhyme(cls, word1: str, word2: str, stress1: str, stress2: str, min_level: int = 2) -> bool:
        """
        בדוק אם שתי מילים מתחרזות בצורה תקינה.
        
        min_level:
        - 1: חרוז מושלם בלבד
        - 2: חרוז טוב (הברה סופית זהה)
        - 3: עיצור משותף
        - 4: תנועה משותפת
        - 5: כל דבר (לא מומלץ)
        """
        key1 = RhymeChecker.extract_rhyme_key(word1, stress1)
        key2 = RhymeChecker.extract_rhyme_key(word2, stress2)
        
        level = RhymeChecker.rhyme_level(key1, key2)
        
        # בדוק חריגים
        if cls._is_phonetic_exception(key1, key2):
            return False
        
        return level <= min_level
    
    @classmethod
    def _is_phonetic_exception(cls, key1: tuple, key2: tuple) -> bool:
        """בדוק אם זה חריג פונטי (false positive)."""
        # בדוק אם יש יוד בהתחלה של אחת המילים
        # ויוד בסוף של השנייה (לא צריך להתחרז)
        
        def has_initial_yod(key):
            """בדוק אם יש יוד בהתחלה."""
            if key and key[0][0] == 'y':
                return True
            return False
        
        def has_final_yod(key):
            """בדוק אם יש יוד בסוף."""
            if key and key[-1][0] == 'y':
                return True
            return False
        
        # אם אחת מתחילה ביוד והשנייה מסתיימת ביוד - זה לא חרוז
        if (has_initial_yod(key1) and has_final_yod(key2)) or \
           (has_initial_yod(key2) and has_final_yod(key1)):
            return True
        
        return False
    
    @classmethod
    def filter_suggestions_by_rhyme(cls, suggestions: list[str], target_word: str, 
                                   target_stress: str, min_level: int = 2) -> list[str]:
        """
        סנן הצעות לפי חריזה תקינה.
        מחזיר רק הצעות שמתחרזות עם target_word.
        """
        filtered = []
        
        for suggestion in suggestions:
            try:
                # קבל ניקוד להצעה
                from services.suggestion_service import _vocalize
                vocalized = _vocalize(suggestion)
                suggestion_stress = StressDetector.detect_stress(vocalized)
                
                # בדוק אם מתחרז
                if cls.is_valid_rhyme(target_word, vocalized, target_stress, 
                                     suggestion_stress, min_level=min_level):
                    filtered.append(suggestion)
            except Exception:
                # אם יש שגיאה, דלג על ההצעה
                continue
        
        return filtered
    
    @classmethod
    def rank_suggestions_by_rhyme_quality(cls, suggestions: list[str], target_word: str,
                                         target_stress: str) -> list[tuple[str, int]]:
        """
        דרג הצעות לפי איכות החרוז.
        מחזיר רשימה של (הצעה, רמה) כאשר 1 = הטוב ביותר.
        """
        ranked = []
        
        for suggestion in suggestions:
            try:
                from services.suggestion_service import _vocalize
                vocalized = _vocalize(suggestion)
                suggestion_stress = StressDetector.detect_stress(vocalized)
                
                key1 = RhymeChecker.extract_rhyme_key(target_word, target_stress)
                key2 = RhymeChecker.extract_rhyme_key(vocalized, suggestion_stress)
                
                level = RhymeChecker.rhyme_level(key1, key2)
                
                # דלג על חריגים
                if cls._is_phonetic_exception(key1, key2):
                    continue
                
                ranked.append((suggestion, level))
            except Exception:
                continue
        
        # מיין לפי רמה (1 = הטוב ביותר)
        ranked.sort(key=lambda x: x[1])
        return ranked
    
    @classmethod
    def get_rhyme_explanation(cls, word1: str, word2: str, stress1: str, stress2: str) -> dict:
        """
        קבל הסבר מפורט על מדוע שתי מילים מתחרזות או לא.
        """
        key1 = RhymeChecker.extract_rhyme_key(word1, stress1)
        key2 = RhymeChecker.extract_rhyme_key(word2, stress2)
        
        level = RhymeChecker.rhyme_level(key1, key2)
        
        details1 = cls.get_detailed_phonemes(word1, stress1)
        details2 = cls.get_detailed_phonemes(word2, stress2)
        
        is_exception = cls._is_phonetic_exception(key1, key2)
        
        return {
            'word1': word1,
            'word2': word2,
            'rhyme_level': level,
            'is_valid_rhyme': level <= 2 and not is_exception,
            'is_phonetic_exception': is_exception,
            'details1': details1,
            'details2': details2,
            'explanation': cls._get_explanation(level, is_exception),
        }
    
    @classmethod
    def _get_explanation(cls, level: int, is_exception: bool) -> str:
        """קבל הסבר טקסטואלי."""
        if is_exception:
            return "חריג פונטי - לא מתחרז למרות דמיון"
        
        explanations = {
            1: "חרוז מושלם - הברה סופית זהה לחלוטין",
            2: "חרוז טוב - הברה סופית זהה (תנועה + עיצורים סופיים)",
            3: "עיצור משותף - עיצורים סופיים זהים אבל תנועה שונה",
            4: "תנועה משותפת - תנועה סופית זהה אבל עיצורים שונים",
            5: "אין חרוז - לא מתחרז",
        }
        
        return explanations.get(level, "לא ידוע")
    
    @classmethod
    def validate_poem_rhyme_scheme(cls, lines: list[str], metadata: list[dict]) -> dict:
        """
        בדוק תבנית חריזה של שיר עם סינון משופר.
        """
        if len(lines) != len(metadata):
            return {'error': 'מספר שורות לא תואם'}
        
        # קבל מפתחות חרוז
        rhyme_keys = []
        for meta in metadata:
            key = RhymeChecker.extract_rhyme_key(
                meta['last_word_vocalized'],
                meta['stress_type']
            )
            rhyme_keys.append(key)
        
        # בדוק חריגים
        issues = []
        for i in range(len(rhyme_keys)):
            for j in range(i + 1, len(rhyme_keys)):
                if RhymeChecker.rhyme_level(rhyme_keys[i], rhyme_keys[j]) <= 2:
                    # בדוק אם זה חריג
                    if cls._is_phonetic_exception(rhyme_keys[i], rhyme_keys[j]):
                        issues.append({
                            'lines': (i + 1, j + 1),
                            'words': (metadata[i]['original_word'], metadata[j]['original_word']),
                            'issue': 'חריג פונטי - לא מתחרז',
                            'level': 'warning',
                        })
        
        return {
            'rhyme_keys': rhyme_keys,
            'issues': issues,
            'is_valid': len(issues) == 0,
        }
