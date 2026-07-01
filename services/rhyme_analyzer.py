"""
מנתח חריזה משופר - תמיכה ב-ABBA וזיהוי מילים עם ניקוד שונה.
"""
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from typing import List, Dict, Tuple


def extract_rhyme_key_normalized(word: str) -> Tuple:
    """
    חלץ מפתח חרוז מנורמל.
    מתעלם מהבדלי ניקוד קטנים (קמץ/פתח, חולם/חולם חסר).
    """
    # קבל מפתח רגיל
    stress = StressDetector.detect_stress(word)
    key = RhymeChecker.extract_rhyme_key(word, stress)
    
    # נרמל את המפתח
    normalized_key = []
    for cons, vowel in key:
        # נרמל תנועות
        if vowel in ['A', 'a']:  # קמץ/פתח
            vowel = 'A'
        elif vowel in ['O', 'o']:  # חולם
            vowel = 'O'
        elif vowel in ['E', 'e']:  # צרה/סגול
            vowel = 'E'
        elif vowel in ['I', 'i']:  # חיריק
            vowel = 'I'
        elif vowel in ['U', 'u']:  # קובוץ
            vowel = 'U'
        
        normalized_key.append((cons, vowel))
    
    return tuple(normalized_key)


def detect_rhyme_pattern(lines: List[str]) -> Dict:
    """
    זהה תבנית חריזה עם תמיכה ב-ABBA.
    """
    if len(lines) < 2:
        return {'pattern': 'לא מוגדר', 'rhyme_pairs': []}
    
    # קבל מפתחות חרוז לכל שורה
    keys = []
    for line in lines:
        words = line.split()
        if words:
            word = words[-1]
            key = extract_rhyme_key_normalized(word)
            keys.append(key)
        else:
            keys.append(tuple())
    
    # זהה תבנית
    if len(lines) == 4:
        # בדוק את כל התבניות האפשריות
        patterns = {
            'AAAA': _check_aaaa(keys),
            'AABB': _check_aabb(keys),
            'ABAB': _check_abab(keys),
            'ABBA': _check_abba(keys),
        }
        
        # בחר את התבנית עם הציון הכי טוב
        best_pattern = max(patterns.items(), key=lambda x: x[1]['score'])
        
        return {
            'pattern': best_pattern[0],
            'rhyme_pairs': best_pattern[1]['pairs'],
            'score': best_pattern[1]['score'],
            'details': best_pattern[1]['details'],
        }
    
    return {'pattern': 'חופשית', 'rhyme_pairs': []}


def _check_aaaa(keys: List[Tuple]) -> Dict:
    """בדוק תבנית AAAA."""
    if len(set(keys)) == 1:
        return {
            'score': 10,
            'pairs': [(0, 1), (1, 2), (2, 3)],
            'details': 'כל השורות מתחרזות'
        }
    return {'score': 0, 'pairs': [], 'details': 'לא AAAA'}


def _check_aabb(keys: List[Tuple]) -> Dict:
    """בדוק תבנית AABB."""
    score = 0
    pairs = []
    
    # בדוק אם שורות 1-2 מתחרזות
    if _is_rhyme(keys[0], keys[1]):
        score += 3
        pairs.append((0, 1))
    
    # בדוק אם שורות 3-4 מתחרזות
    if _is_rhyme(keys[2], keys[3]):
        score += 3
        pairs.append((2, 3))
    
    # בונוס אם זוגות שונים
    if keys[0] != keys[2]:
        score += 2
    
    return {
        'score': score,
        'pairs': pairs,
        'details': f'AABB: {score}/8'
    }


def _check_abab(keys: List[Tuple]) -> Dict:
    """בדוק תבנית ABAB."""
    score = 0
    pairs = []
    
    # בדוק אם שורות 1-3 מתחרזות
    if _is_rhyme(keys[0], keys[2]):
        score += 3
        pairs.append((0, 2))
    
    # בדוק אם שורות 2-4 מתחרזות
    if _is_rhyme(keys[1], keys[3]):
        score += 3
        pairs.append((1, 3))
    
    # בונוס אם זוגות שונים
    if keys[0] != keys[1]:
        score += 2
    
    return {
        'score': score,
        'pairs': pairs,
        'details': f'ABAB: {score}/8'
    }


def _check_abba(keys: List[Tuple]) -> Dict:
    """בדוק תבנית ABBA."""
    score = 0
    pairs = []
    
    # בדוק אם שורות 1-4 מתחרזות (A)
    if _is_rhyme(keys[0], keys[3]):
        score += 3
        pairs.append((0, 3))
    
    # בדוק אם שורות 2-3 מתחרזות (B)
    if _is_rhyme(keys[1], keys[2]):
        score += 3
        pairs.append((1, 2))
    
    # בונוס אם זוגות שונים
    if keys[0] != keys[1]:
        score += 2
    
    return {
        'score': score,
        'pairs': pairs,
        'details': f'ABBA: {score}/8'
    }


def _is_rhyme(key1: Tuple, key2: Tuple) -> bool:
    """בדוק אם שני מפתחות מתחרזים (רמה 1-2)."""
    if not key1 or not key2:
        return False
    
    level = RhymeChecker.rhyme_level(key1, key2)
    return level <= 2


def suggest_rhyme_improvements(lines: List[str]) -> Dict:
    """
    הצע שיפורים לחריזה לפי התבנית שזוהתה.
    """
    analysis = detect_rhyme_pattern(lines)
    
    improvements = []
    
    if analysis['pattern'] == 'ABBA':
        # עבור ABBA, צריך לשפר את שורות 1,4 ושורות 2,3
        if (0, 3) in analysis['rhyme_pairs'] and (1, 2) in analysis['rhyme_pairs']:
            improvements.append({
                'type': 'ABBA תקין',
                'lines': [(1, 4), (2, 3)],
                'status': 'תקין'
            })
        else:
            improvements.append({
                'type': 'ABBA לא שלם',
                'lines': [(1, 4), (2, 3)],
                'status': 'דורש שיפור'
            })
    
    elif analysis['pattern'] == 'AABB':
        improvements.append({
            'type': 'AABB תקין',
            'lines': [(1, 2), (3, 4)],
            'status': 'תקין'
        })
    
    elif analysis['pattern'] == 'ABAB':
        improvements.append({
            'type': 'ABAB תקין',
            'lines': [(1, 3), (2, 4)],
            'status': 'תקין'
        })
    
    return {
        'pattern': analysis['pattern'],
        'score': analysis['score'],
        'improvements': improvements,
    }


def normalize_word_for_rhyme(word: str) -> str:
    """
    נרמל מילה לצורך חריזה.
    מתעלם מהבדלי ניקוד קטנים.
    """
    # הסר ניקוד לא חיוני
    normalized = ''
    for char in word:
        # קמץ ופתח נחשבים אותו דבר
        if char == '\u05B8':  # קמץ
            normalized += '\u05B7'  # המר לפתח
        else:
            normalized += char
    
    return normalized
