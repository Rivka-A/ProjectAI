"""
מחולל שורות - יצירת שורות שלמות שמתחרזות.
"""
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector
from services.bert_service import get_fill_mask_suggestions
from typing import List, Tuple


def generate_rhyming_lines(
    content_idea: str,
    target_key: Tuple,
    pattern: str = None,
    num_suggestions: int = 5
) -> List[dict]:
    """חולל שורות שלמות שמתחרזות עם מפתח חרוז מסוים."""
    suggestions = []
    masked_line = f"{content_idea} [MASK]"
    try:
        raw_suggestions = get_fill_mask_suggestions([masked_line], 0, "[MASK]", top_k=50)
        for word in raw_suggestions:
            from services.improved_suggestion_service import _vocalize
            try:
                vocalized = _vocalize(word)
                sug_key = RhymeChecker.extract_rhyme_key(vocalized, StressDetector.detect_stress(vocalized))
                level = RhymeChecker.rhyme_level(sug_key, target_key)
                if level <= 5:
                    suggestions.append({
                        'line': f"{content_idea} {word}",
                        'last_word': word,
                        'level': level,
                        'method': 'BERT mask',
                    })
            except Exception as e:
                print(f"Error processing suggestion '{word}': {e} line_generator 54")
                continue
        suggestions.sort(key=lambda x: x['level'])
        return suggestions[:num_suggestions]
    except Exception as e:
        print(f"שגיאה: {e} line_generator 63")
        return []


def rewrite_line_for_rhyme(
    original_line: str,
    target_key: Tuple,
    preserve_meaning: bool = True,
    num_suggestions: int = 5
) -> List[dict]:
    """שכתב שורה קיימת כדי שתתחרז עם מפתח חרוז מסוים."""
    suggestions = []
    suggestions.extend(_replace_last_word(original_line, target_key, num_suggestions))
    suggestions.extend(_extend_line(original_line, target_key, num_suggestions))
    suggestions.extend(_reorder_words(original_line, target_key, num_suggestions))
    suggestions.sort(key=lambda x: (x['level'], x.get('quality', 5)))
    return suggestions[:num_suggestions]


def _replace_last_word(line: str, target_key: Tuple, num: int) -> List[dict]:
    """החלף את המילה האחרונה."""
    suggestions = []
    words = line.split()
    if not words:
        return []
    original_last = words[-1]
    original_last_letters = "".join(c for c in original_last if '\u05D0' <= c <= '\u05EA')
    masked_line = ' '.join(words[:-1]) + ' [MASK]'
    try:
        raw_suggestions = get_fill_mask_suggestions([masked_line], 0, '[MASK]', top_k=50)
        for word in raw_suggestions:
            word_letters = "".join(c for c in word if '\u05D0' <= c <= '\u05EA')
            if word_letters == original_last_letters:
                continue
            from services.improved_suggestion_service import _vocalize
            try:
                vocalized = _vocalize(word)
                sug_key = RhymeChecker.extract_rhyme_key(vocalized, StressDetector.detect_stress(vocalized))
                level = RhymeChecker.rhyme_level(sug_key, target_key)
                if level <= 5:
                    suggestions.append({
                        'line': ' '.join(words[:-1] + [word]),
                        'method': 'החלפת מילה אחרונה',
                        'last_word': word,
                        'level': level,
                        'quality': 1,
                    })
            except Exception as e:
                print(f"Error processing suggestion '{word}': {e} line_generator 145")
                continue
        return suggestions
    except Exception as e:
        print(f"Error in _replace_last_word for line: {line}: {e} line_generator 150")
        return []


def _extend_line(line: str, target_key: Tuple, num: int) -> List[dict]:
    """הוסף מילים אחרי המילה האחרונה."""
    suggestions = []
    extended_line = f"{line} [MASK]"
    try:
        raw_suggestions = get_fill_mask_suggestions([extended_line], 0, '[MASK]', top_k=50)
        for word in raw_suggestions:
            from services.improved_suggestion_service import _vocalize
            try:
                vocalized = _vocalize(word)
                sug_key = RhymeChecker.extract_rhyme_key(vocalized, StressDetector.detect_stress(vocalized))
                level = RhymeChecker.rhyme_level(sug_key, target_key)
                if level <= 5:
                    suggestions.append({
                        'line': f"{line} {word}",
                        'method': 'הוספת מילה',
                        'last_word': word,
                        'level': level,
                        'quality': 2,
                    })
            except Exception as e:
                print(f"Error processing suggestion '{word}': {e} line_generator 185")
                continue
        return suggestions
    except Exception as e:
        print(f"Error in _extend_line for line: {line}: {e} line_generator 191")
        return []


def _reorder_words(line: str, target_key, num: int) -> list:
    """נסה סדרי מילים שונים כדי שהמילה האחרונה תתחרז."""
    from itertools import permutations
    from services.improved_suggestion_service import _vocalize

    words = line.split()
    if len(words) < 2 or len(words) > 6:
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
            sug_key = RhymeChecker.extract_rhyme_key(voc, StressDetector.detect_stress(voc))
            level = RhymeChecker.rhyme_level(sug_key, target_key)
            if level <= 5:
                suggestions.append({
                    'line': ' '.join(perm),
                    'method': 'שינוי סדר מילים',
                    'last_word': last_word,
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
    target_key: Tuple,
    variation_type: str = 'all'
) -> dict:
    """הצע וריאציות שונות של שורה להתאמת חריזה."""
    all_variations = []
    if variation_type in ['last_word', 'all']:
        all_variations.extend(_replace_last_word(line, target_key, 10))
    if variation_type in ['extend', 'all']:
        all_variations.extend(_extend_line(line, target_key, 10))
    all_variations.sort(key=lambda x: (x['level'], x.get('quality', 5)))
    return {'original': line, 'variations': all_variations[:15]}


def create_line_from_idea(
    idea: str,
    target_key: Tuple,
    style: str = 'poetic'
) -> List[dict]:
    """צור שורה חדשה מרעיון עם חריזה מתאימה."""
    masked_line = f"{idea} [MASK]"
    suggestions = []
    try:
        raw_suggestions = get_fill_mask_suggestions([masked_line], 0, '[MASK]', top_k=50)
        for word in raw_suggestions:
            from services.improved_suggestion_service import _vocalize
            try:
                vocalized = _vocalize(word)
                sug_key = RhymeChecker.extract_rhyme_key(vocalized, StressDetector.detect_stress(vocalized))
                level = RhymeChecker.rhyme_level(sug_key, target_key)
                if level <= 3:
                    suggestions.append({
                        'line': f"{idea} {word}",
                        'last_word': word,
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
