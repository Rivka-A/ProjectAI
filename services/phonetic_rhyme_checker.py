"""
בודק חרוז נכון - לפי סיומת פונטית בלבד.
"""
from core.rhyme_checker import RhymeChecker
from core.stress_detector import StressDetector


def get_phonetic_suffix(word_vocalized: str, stress: str) -> tuple:
    key = RhymeChecker.extract_rhyme_key(word_vocalized, stress)
    if not key:
        return ('', ())
    last_vowel = ''
    vowel_index = -1
    for i in range(len(key) - 1, -1, -1):
        if key[i][1]:
            last_vowel = key[i][1]
            vowel_index = i
            break
    if not last_vowel:
        return ('', ())
    consonants = [key[i][0] for i in range(vowel_index + 1, len(key)) if key[i][0]]
    return (last_vowel, tuple(consonants))


def compare_phonetic_suffixes(suffix1: tuple, suffix2: tuple) -> int:
    """
    1 = חרוז מושלם  (תנועה + עיצורים סופיים זהים)
    2 = חרוז טוב    (תנועה זהה, עיצורים סופיים זהים, עיצור נושא שונה)
    3 = עיצור משותף (תנועה זהה, עיצורים סופיים שייכים לאותה קבוצת מוצא)
    4 = תנועה משותפת (שתיהן פתוחות — אין עיצור סופי)
    5 = לא חרוז
    """
    vowel1, cons1 = suffix1
    vowel2, cons2 = suffix2

    if not vowel1 or not vowel2:
        return 5
    if vowel1 != vowel2:
        return 5

    # תנועה זהה
    if cons1 == cons2:
        return 1

    if not cons1 and not cons2:
        return 4  # שתיהן פתוחות

    if cons1 and cons2:
        def get_group(c):
            for name, phonemes in RhymeChecker.source.items():
                if c in phonemes:
                    return name
            return None
        if get_group(cons1[0]) == get_group(cons2[0]) and get_group(cons1[0]) is not None:
            return 3

    return 5


def is_rhyme(word1_vocalized: str, word2_vocalized: str, min_level: int = 2) -> bool:
    stress1 = StressDetector.detect_stress(word1_vocalized)
    stress2 = StressDetector.detect_stress(word2_vocalized)
    suffix1 = get_phonetic_suffix(word1_vocalized, stress1)
    suffix2 = get_phonetic_suffix(word2_vocalized, stress2)
    return compare_phonetic_suffixes(suffix1, suffix2) <= min_level


def get_rhyme_quality(word1_vocalized: str, word2_vocalized: str) -> dict:
    stress1 = StressDetector.detect_stress(word1_vocalized)
    stress2 = StressDetector.detect_stress(word2_vocalized)
    suffix1 = get_phonetic_suffix(word1_vocalized, stress1)
    suffix2 = get_phonetic_suffix(word2_vocalized, stress2)
    level = compare_phonetic_suffixes(suffix1, suffix2)
    explanations = {
        1: "חרוז מושלם - תנועה ועיצורים זהים",
        2: "חרוז טוב - תנועה זהה, עיצורים סופיים זהים",
        3: "עיצור משותף - תנועה זהה, קבוצת מוצא זהה",
        4: "תנועה משותפת - שתיהן פתוחות",
        5: "אין חרוז",
    }
    return {
        'is_rhyme': level <= 3,
        'level': level,
        'suffix1': suffix1,
        'suffix2': suffix2,
        'explanation': explanations.get(level, "אין חרוז"),
    }


def filter_rhyming_words(words: list, target_word_vocalized: str, min_level: int = 2) -> list:
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
            if level <= 3:
                ranked.append((word, level))
        except:
            continue
    ranked.sort(key=lambda x: x[1])
    return ranked
