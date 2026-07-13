"""
מחולל שורות - יצירת שורות שלמות שמתחרזות.
"""
from services.phonetic_rhyme_checker import get_phonetic_suffix, compare_phonetic_suffixes
from services.bert_service import get_fill_mask_suggestions
from typing import List, Tuple


def generate_rhyming_lines(
    content_idea: str,
    target_suffix: Tuple,
    pattern: str = None,
    num_suggestions: int = 5
) -> List[dict]:
    """
    חולל שורות שלמות שמתחרזות עם סיומת פונטית מסוימת.
    
    Args:
        content_idea: רעיון התוכן של השורה
        target_suffix: הסיומת הפונטית הרצויה (תנועה, עיצורים)
        pattern: תבנית חריזה (AABB, ABAB, ABBA)
        num_suggestions: מספר הצעות
    
    Returns:
        list של שורות עם מטא-דאטה
    """
    suggestions = []
    
    # שיטה 1: שימוש ב-BERT עם mask בסוף
    masked_line = f"{content_idea} [MASK]"
    
    try:
        raw_suggestions = get_fill_mask_suggestions([masked_line], 0, "[MASK]", top_k=50)
        
        for word in raw_suggestions:
            # בדוק אם המילה מתחרזת
            from services.improved_suggestion_service import _vocalize
            from core.stress_detector import StressDetector
            
            try:
                vocalized = _vocalize(word)
                suffix = get_phonetic_suffix(vocalized, StressDetector.detect_stress(vocalized))
                level = compare_phonetic_suffixes(suffix, target_suffix)
                
                if level <= 2:  # רק חרוז טוב
                    suggestions.append({
                        'line': f"{content_idea} {word}",
                        'last_word': word,
                        'suffix': suffix,
                        'level': level,
                        'method': 'BERT mask',
                    })
            except Exception as e:
                print(f"Error processing suggestion '{word}': {e} line_generator 54")
                continue
        
        # מיין לפי רמת חרוז
        suggestions.sort(key=lambda x: x['level'])
        
        return suggestions[:num_suggestions]
    
    except Exception as e:
        print(f"שגיאה: {e} line_generator 63")
        return []


def rewrite_line_for_rhyme(
    original_line: str,
    target_suffix: Tuple,
    preserve_meaning: bool = True,
    num_suggestions: int = 5
) -> List[dict]:
    """
    שכתב שורה קיימת כדי שתתחרז עם סיומת מסוימת.
    
    שיטות:
    1. שינוי המילה האחרונה
    2. הוספת מילים בסוף
    3. שכתוב השורה עם משמעות דומה
    
    Args:
        original_line: השורה המקורית
        target_suffix: הסיומת הפונטית הרצויה
        preserve_meaning: האם לשמור על המשמעות
        num_suggestions: מספר הצעות
    
    Returns:
        list של שורות משוכתבות
    """
    suggestions = []
    words = original_line.split()
    
    # שיטה 1: החלף רק המילה האחרונה
    last_word_suggestions = _replace_last_word(original_line, target_suffix, num_suggestions)
    suggestions.extend(last_word_suggestions)
    
    # שיטה 2: הוסף מילים אחרי המילה האחרונה
    extended_suggestions = _extend_line(original_line, target_suffix, num_suggestions)
    suggestions.extend(extended_suggestions)
    
    # שיטה 3: שינוי סדר מילים
    reorder_suggestions = _reorder_words(original_line, target_suffix, num_suggestions)
    suggestions.extend(reorder_suggestions)
    
    # מיין לפי רמת חרוז ואיכות
    suggestions.sort(key=lambda x: (x['level'], x.get('quality', 5)))
    
    return suggestions[:num_suggestions]


def _replace_last_word(line: str, target_suffix: Tuple, num: int) -> List[dict]:
    """החלף את המילה האחרונה."""
    suggestions = []
    words = line.split()
    
    if not words:
        return []
    
    # קבל הצעות למילה האחרונה
    masked_line = ' '.join(words[:-1]) + ' [MASK]'
    
    try:
        raw_suggestions = get_fill_mask_suggestions([masked_line], 0, '[MASK]', top_k=50)
        
        for word in raw_suggestions:
            from services.improved_suggestion_service import _vocalize
            from core.stress_detector import StressDetector
            
            try:
                vocalized = _vocalize(word)
                suffix = get_phonetic_suffix(vocalized, StressDetector.detect_stress(vocalized))
                level = compare_phonetic_suffixes(suffix, target_suffix)
                
                if level <= 2:
                    new_line = ' '.join(words[:-1] + [word])
                    suggestions.append({
                        'line': new_line,
                        'method': 'החלפת מילה אחרונה',
                        'last_word': word,
                        'suffix': suffix,
                        'level': level,
                        'quality': 1,  # איכות טובה - שינוי מינימלי
                    })
            except Exception as e:
                print(f"Error processing suggestion '{word}': {e} line_generator 145")
                continue
        
        return suggestions
    
    except Exception as e:
        print(f"Error in _replace_last_word for line: {line}: {e} line_generator 150")
        print(f"Error in _replace_last_word for line: {line}")
        return []


def _extend_line(line: str, target_suffix: Tuple, num: int) -> List[dict]:
    """הוסף מילים אחרי המילה האחרונה."""
    suggestions = []
    
    # הוסף mask אחרי השורה
    extended_line = f"{line} [MASK]"
    
    try:
        raw_suggestions = get_fill_mask_suggestions([extended_line], 0, '[MASK]', top_k=50)
        
        for word in raw_suggestions:
            from services.improved_suggestion_service import _vocalize
            from core.stress_detector import StressDetector
            
            try:
                vocalized = _vocalize(word)
                suffix = get_phonetic_suffix(vocalized, StressDetector.detect_stress(vocalized))
                level = compare_phonetic_suffixes(suffix, target_suffix)
                
                if level <= 2:
                    new_line = f"{line} {word}"
                    suggestions.append({
                        'line': new_line,
                        'method': 'הוספת מילה',
                        'last_word': word,
                        'suffix': suffix,
                        'level': level,
                        'quality': 2,  # איכות בינונית
                    })
            except Exception as e:
                print(f"Error processing suggestion '{word}': {e} line_generator 185")
                continue
        
        return suggestions
    
    except Exception as e:
        print(f"Error in _extend_line for line: {line}: {e} line_generator 191")
        return []


def _reorder_words(line: str, target_suffix, num: int) -> list:
    """נסה סדרי מילים שונים כדי שהמילה האחרונה תתחרז."""
    from itertools import permutations
    from services.improved_suggestion_service import _vocalize
    from core.stress_detector import StressDetector

    words = line.split()
    if len(words) < 2 or len(words) > 6:  # מעל 6 מילים — יותר מדי תמורות
        return []

    suggestions = []
    seen = set()
    original_tuple = tuple(words)

    for perm in permutations(words):
        if perm == original_tuple:
            continue
        last_word = perm[-1]
        if last_word in seen:
            continue
        seen.add(last_word)
        try:
            voc = _vocalize(last_word)
            suffix = get_phonetic_suffix(voc, StressDetector.detect_stress(voc))
            level = compare_phonetic_suffixes(suffix, target_suffix)
            if level <= 2:
                suggestions.append({
                    'line': ' '.join(perm),
                    'method': 'שינוי סדר מילים',
                    'last_word': last_word,
                    'suffix': suffix,
                    'level': level,
                    'quality': 1,
                })
        except Exception as e:
            print(f"Error processing suggestion '{last_word}': {e} line_generator 85")
            continue

    suggestions.sort(key=lambda x: x['level'])
    return suggestions[:num]



def suggest_line_variations(
    line: str,
    target_suffix: Tuple,
    variation_type: str = 'all'
) -> dict:
    """
    הצע וריאציות שונות של שורה להתאמת חריזה.
    
    Args:
        line: השורה המקורית
        target_suffix: הסיומת הרצויה
        variation_type: סוג וריאציה
            - 'last_word': רק החלפת מילה אחרונה
            - 'extend': רק הוספת מילים
            - 'rewrite': רק שכתוב
            - 'all': כל השיטות
    
    Returns:
        {
            'original': str,
            'variations': [
                {
                    'line': str,
                    'method': str,
                    'level': int,
                    'quality': int,
                }
            ]
        }
    """
    all_variations = []
    
    if variation_type in ['last_word', 'all']:
        variations = _replace_last_word(line, target_suffix, 10)
        all_variations.extend(variations)
    
    if variation_type in ['extend', 'all']:
        variations = _extend_line(line, target_suffix, 10)
        all_variations.extend(variations)
    
    if variation_type in ['rewrite', 'all']:
        variations = _rewrite_line(line, target_suffix, 10)
        all_variations.extend(variations)
    
    # מיין לפי איכות ורמת חרוז
    all_variations.sort(key=lambda x: (x['level'], x['quality']))
    
    return {
        'original': line,
        'variations': all_variations[:15],
    }


def create_line_from_idea(
    idea: str,
    target_suffix: Tuple,
    style: str = 'poetic'
) -> List[dict]:
    """
    צור שורה חדשה מרעיון עם חריזה מתאימה.
    
    Args:
        idea: הרעיון/תוכן
        target_suffix: הסיומת הרצויה
        style: סגנון (poetic, casual, formal)
    
    Returns:
        list של הצעות שורות
    """
    # לעת עתה, שיטה פשוטה עם BERT
    masked_line = f"{idea} [MASK]"
    
    suggestions = []
    
    try:
        raw_suggestions = get_fill_mask_suggestions([masked_line], 0, '[MASK]', top_k=50)
        
        for word in raw_suggestions:
            from services.improved_suggestion_service import _vocalize
            from core.stress_detector import StressDetector
            
            try:
                vocalized = _vocalize(word)
                suffix = get_phonetic_suffix(vocalized, StressDetector.detect_stress(vocalized))
                level = compare_phonetic_suffixes(suffix, target_suffix)
                
                if level <= 3:
                    new_line = f"{idea} {word}"
                    suggestions.append({
                        'line': new_line,
                        'last_word': word,
                        'suffix': suffix,
                        'level': level,
                        'style': style,
                    })
            except Exception as e:
                print(f"Error processing suggestion '{word}': {e} line_generator 334")
                continue
        
        suggestions.sort(key=lambda x: x['level'])
        return suggestions[:10]
    
    except Exception as e:
        print(f"Error in create_line_from_idea: {e} line_generator 341")
        return []
