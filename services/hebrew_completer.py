"""
מודול להשלמת משפטים בעברית ותיקוף תחבירי.
"""
import re
from typing import Optional


class HebrewSentenceCompleter:
    """משלים משפטים קטועים לביטויים תקינים תחבירית בעברית."""
    
    # דפוסי משפטים נפוצים בעברית
    COMMON_PATTERNS = {
        'verb_ending': [
            'ים', 'ות', 'ה', 'י', 'ו', 'ן', 'ת'
        ],
        'noun_endings': [
            'ים', 'ות', 'ה', 'י', 'ו', 'ן', 'ת', 'ית'
        ],
        'prepositions': [
            'את', 'של', 'ל', 'מ', 'ב', 'כ', 'ה', 'ו'
        ]
    }
    
    @staticmethod
    def is_complete_word(word: str) -> bool:
        """בדוק אם המילה שלמה (לא קטועה)."""
        if not word:
            return False
        # מילה קטועה בדרך כלל קצרה מדי או מסתיימת בעיצור בודד
        hebrew_letters = re.findall(r'[\u05D0-\u05EA]', word)
        return len(hebrew_letters) >= 2
    
    @staticmethod
    def suggest_completion(partial_word: str) -> list[str]:
        """הצע השלמות אפשריות למילה קטועה."""
        if not partial_word or len(partial_word) < 2:
            return []
        
        suggestions = []
        # הוסף סיומות נפוצות
        for ending in HebrewSentenceCompleter.COMMON_PATTERNS['verb_ending']:
            suggestions.append(partial_word + ending)
        
        return suggestions[:5]
    
    @staticmethod
    def validate_sentence_structure(sentence: str) -> bool:
        """בדוק אם המשפט בעל מבנה תקין בעברית."""
        if not sentence.strip():
            return False
        
        words = sentence.split()
        if len(words) < 2:
            return False
        
        # בדוק שיש לפחות מילה אחת שלמה
        complete_words = [w for w in words if HebrewSentenceCompleter.is_complete_word(w)]
        return len(complete_words) >= len(words) * 0.7  # לפחות 70% מילים שלמות
    
    @staticmethod
    def fix_broken_line(line: str) -> str:
        """תקן שורה קטועה."""
        if not line.strip():
            return line
        
        words = line.split()
        fixed_words = []
        
        for word in words:
            if HebrewSentenceCompleter.is_complete_word(word):
                fixed_words.append(word)
            else:
                # נסה להשלים מילה קטועה
                suggestions = HebrewSentenceCompleter.suggest_completion(word)
                if suggestions:
                    fixed_words.append(suggestions[0])
                else:
                    fixed_words.append(word)
        
        return " ".join(fixed_words)
    
    @staticmethod
    def extract_rhyme_word(line: str) -> Optional[str]:
        """חלץ את המילה האחרונה (למטרות חרוז)."""
        words = line.split()
        if words:
            return words[-1]
        return None
    
    @staticmethod
    def ensure_grammatical_agreement(word: str, context: str) -> str:
        """וודא הסכמה דקדוקית עם ההקשר."""
        # בדוק אם המילה צריכה להיות בנקבה או זכר בהתאם להקשר
        if 'ה' in context or 'היא' in context:
            # הקשר נקבה
            if word.endswith('ים'):
                return word[:-2] + 'ות'
        elif 'הוא' in context or 'הם' in context:
            # הקשר זכר
            if word.endswith('ות'):
                return word[:-2] + 'ים'
        
        return word
