"""
בודק חרוז נכון - לפי סיומת פונטית בלבד.
"""
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector


def get_phonetic_suffix(word_vocalized: str, stress: str) -> tuple:
    """
    חלץ את הסיומת הפונטית של המילה.
    
    הסיומת הפונטית = תנועה אחרונה + כל העיצורים שאחריה
    
    דוגמאות:
    - "קָטוּעַ" → ('A', ('',))  # עיצור עין + תנועת פתח
    - "שָׁבוּר" → ('U', ('r',))  # עיצור ריש + תנועת שורוק
    - "מַיִם" → ('I', ('m',))   # עיצור מ"ם + תנועת חיריק (אחרי יוד)
    
    Returns:
        tuple: (תנועה_אחרונה, tuple_של_עיצורים_אחריה)
    """
    key = RhymeChecker.extract_rhyme_key(word_vocalized, stress)
    
    if not key:
        return ('', ())
    
    # מצא את התנועה האחרונה
    last_vowel = ''
    vowel_index = -1
    
    for i in range(len(key) - 1, -1, -1):
        if key[i][1]:  # תנועה לא ריקה
            last_vowel = key[i][1]
            vowel_index = i
            break
    
    if not last_vowel:
        return ('', ())
    
    # אסוף את כל העיצורים אחרי התנועה
    consonants = []
    for i in range(vowel_index + 1, len(key)):
        if key[i][0]:  # עיצור לא ריק
            consonants.append(key[i][0])
    
    return (last_vowel, tuple(consonants))


def compare_phonetic_suffixes(suffix1: tuple, suffix2: tuple) -> int:
    """
    השווה שתי סיומות פונטיות.
    
    Returns:
        1 - חרוז מושלם (תנועה + עיצורים זהים)
        2 - חרוז טוב (תנועה זהה, עיצור אחד שונה)
        3 - חרוז בינוני (תנועה זהה, עיצורים שונים)
        4 - אין חרוז (תנועה שונה)
    """
    vowel1, cons1 = suffix1
    vowel2, cons2 = suffix2
    
    # אין תנועה = אין חרוז
    if not vowel1 or not vowel2:
        return 4
    
    # תנועה שונה = אין חרוז
    if vowel1 != vowel2:
        return 4
    
    # תנועה זהה
    # בדוק עיצורים
    if cons1 == cons2:
        return 1  # חרוז מושלם
    
    # בדוק אם יש עיצור משותף אחד לפחות
    if cons1 and cons2:
        # אם יש עיצור אחד משותף
        if len(cons1) == 1 and len(cons2) == 1:
            if cons1[0] == cons2[0]:
                return 1  # עיצור זהה
            else:
                return 3  # עיצור שונה
        else:
            # בדוק אם העיצור האחרון זהה
            if cons1[-1] == cons2[-1]:
                return 2  # עיצור אחרון זהה
            else:
                return 3  # עיצורים שונים
    
    # רק תנועה זהה
    return 3


def is_rhyme(word1_vocalized: str, word2_vocalized: str, min_level: int = 2) -> bool:
    """
    בדוק אם שתי מילים מתחרזות לפי סיומת פונטית.
    
    Args:
        word1_vocalized: מילה ראשונה מנוקדת
        word2_vocalized: מילה שנייה מנוקדת
        min_level: רמת חרוז מינימלית (1=מושלם, 2=טוב, 3=בינוני)
    
    Returns:
        True אם המילים מתחרזות
    """
    stress1 = StressDetector.detect_stress(word1_vocalized)
    stress2 = StressDetector.detect_stress(word2_vocalized)
    
    suffix1 = get_phonetic_suffix(word1_vocalized, stress1)
    suffix2 = get_phonetic_suffix(word2_vocalized, stress2)
    
    level = compare_phonetic_suffixes(suffix1, suffix2)
    
    return level <= min_level


def get_rhyme_quality(word1_vocalized: str, word2_vocalized: str) -> dict:
    """
    קבל איכות חרוז בין שתי מילים.
    
    Returns:
        {
            'is_rhyme': bool,
            'level': int (1-4),
            'suffix1': tuple,
            'suffix2': tuple,
            'explanation': str,
        }
    """
    stress1 = StressDetector.detect_stress(word1_vocalized)
    stress2 = StressDetector.detect_stress(word2_vocalized)
    
    suffix1 = get_phonetic_suffix(word1_vocalized, stress1)
    suffix2 = get_phonetic_suffix(word2_vocalized, stress2)
    
    level = compare_phonetic_suffixes(suffix1, suffix2)
    
    explanations = {
        1: "חרוז מושלם - תנועה ועיצורים זהים",
        2: "חרוז טוב - תנועה זהה, עיצור אחרון זהה",
        3: "חרוז בינוני - תנועה זהה בלבד",
        4: "אין חרוז - תנועה שונה",
    }
    
    return {
        'is_rhyme': level <= 3,
        'level': level,
        'suffix1': suffix1,
        'suffix2': suffix2,
        'explanation': explanations[level],
    }


def filter_rhyming_words(words: list, target_word_vocalized: str, min_level: int = 2) -> list:
    """
    סנן רשימת מילים לפי חריזה.
    
    Args:
        words: רשימת מילים לסינון
        target_word_vocalized: מילת יעד מנוקדת
        min_level: רמת חרוז מינימלית
    
    Returns:
        רשימת מילים שמתחרזות
    """
    from services.improved_suggestion_service import _vocalize
    
    filtered = []
    
    for word in words:
        try:
            vocalized = _vocalize(word)
            if is_rhyme(target_word_vocalized, vocalized, min_level=min_level):
                filtered.append(word)
        except:
            continue
    
    return filtered


def rank_words_by_rhyme(words: list, target_word_vocalized: str) -> list:
    """
    דרג מילים לפי איכות חרוז.
    
    Returns:
        list של (מילה, רמה) ממוין לפי רמה (1 = טוב ביותר)
    """
    from services.improved_suggestion_service import _vocalize
    
    ranked = []
    
    for word in words:
        try:
            vocalized = _vocalize(word)
            stress = StressDetector.detect_stress(vocalized)
            suffix = get_phonetic_suffix(vocalized, stress)
            target_stress = StressDetector.detect_stress(target_word_vocalized)
            target_suffix = get_phonetic_suffix(target_word_vocalized, target_stress)
            
            level = compare_phonetic_suffixes(suffix, target_suffix)
            
            if level <= 3:  # רק אם יש חרוז
                ranked.append((word, level))
        except:
            continue
    
    # מיין לפי רמה
    ranked.sort(key=lambda x: x[1])
    
    return ranked
