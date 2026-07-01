"""
דוגמאות - בדיקת סיומת פונטית נכונה.
"""


def example_1_phonetic_suffix():
    """דוגמה 1: הבדל בין בדיקה ישנה לחדשה."""
    from services.phonetic_rhyme_checker import get_phonetic_suffix, compare_phonetic_suffixes
    from core.rhyme_checker import RhymeChecker
    
    print("=" * 70)
    print("דוגמה 1: בדיקת סיומת פונטית")
    print("=" * 70)
    
    # מילים שלא צריכות להתחרז
    word1 = "מַיִם"  # מים
    word2 = "יָמִים"  # ימים
    
    print(f"\nמילה 1: {word1}")
    print(f"מילה 2: {word2}")
    
    # בדיקה ישנה (לא נכונה)
    print("\n--- בדיקה ישנה (לפי מפתח חרוז רגיל) ---")
    key1_old = RhymeChecker.extract_rhyme_key(word1, "מלרע")
    key2_old = RhymeChecker.extract_rhyme_key(word2, "מלרע")
    level_old = RhymeChecker.rhyme_level(key1_old, key2_old)
    
    print(f"מפתח 1: {key1_old}")
    print(f"מפתח 2: {key2_old}")
    print(f"רמת חרוז: {level_old}")
    print(f"האם מתחרזים? {'כן (לא נכון!)' if level_old <= 2 else 'לא'}")
    
    # בדיקה חדשה (נכונה)
    print("\n--- בדיקה חדשה (לפי סיומת פונטית) ---")
    suffix1 = get_phonetic_suffix(word1, "מלרע")
    suffix2 = get_phonetic_suffix(word2, "מלרע")
    level_new = compare_phonetic_suffixes(suffix1, suffix2)
    
    print(f"סיומת 1: {suffix1}")  # (תנועה, (עיצורים))
    print(f"סיומת 2: {suffix2}")
    print(f"רמת חרוז: {level_new} (4 = אין חרוז)")
    print(f"האם מתחרזים? {'כן' if level_new <= 2 else 'לא (נכון!)'}")


def example_2_correct_rhyme():
    """דוגמה 2: חרוז נכון."""
    from services.phonetic_rhyme_checker import get_phonetic_suffix, compare_phonetic_suffixes
    
    print("\n" + "=" * 70)
    print("דוגמה 2: חרוז נכון")
    print("=" * 70)
    
    # מילים שכן צריכות להתחרז
    word1 = "קָטוּעַ"
    word2 = "שָׁבוּר"
    
    print(f"\nמילה 1: {word1}")
    print(f"מילה 2: {word2}")
    
    suffix1 = get_phonetic_suffix(word1, "מלרע")
    suffix2 = get_phonetic_suffix(word2, "מלרע")
    level = compare_phonetic_suffixes(suffix1, suffix2)
    
    print(f"\nסיומת 1: {suffix1}")
    print(f"סיומת 2: {suffix2}")
    print(f"רמת חרוז: {level} (1 = מושלם)")
    print(f"האם מתחרזים? {'כן (נכון!)' if level <= 2 else 'לא'}")


def example_3_wrong_rhyme():
    """דוגמה 3: מה שנחשב חרוז אבל לא באמת."""
    from services.phonetic_rhyme_checker import get_phonetic_suffix, compare_phonetic_suffixes
    
    print("\n" + "=" * 70)
    print("דוגמה 3: מה שנחשב חרוז אבל לא באמת")
    print("=" * 70)
    
    # מילים שנגמרות באותה אות אבל תנועה שונה
    word1 = "שָׁלוֹם"  # שלום - חולם
    word2 = "דָּם"     # דם - קמץ
    
    print(f"\nמילה 1: {word1} (תנועה: חולם)")
    print(f"מילה 2: {word2} (תנועה: קמץ)")
    print(f"שתיהן נגמרות ב-מ'ם")
    
    suffix1 = get_phonetic_suffix(word1, "מלרע")
    suffix2 = get_phonetic_suffix(word2, "מלרע")
    level = compare_phonetic_suffixes(suffix1, suffix2)
    
    print(f"\nסיומת 1: {suffix1}")
    print(f"סיומת 2: {suffix2}")
    print(f"רמת חרוז: {level} (4 = אין חרוז)")
    print(f"האם מתחרזים? {'כן' if level <= 2 else 'לא (נכון! תנועה שונה)'}")


def example_4_improve_poem():
    """דוגמה 4: שיפור שיר עם בדיקה נכונה."""
    from poem_improver_final import improve_poem_correct
    
    poem = [
        "הלב קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("\n" + "=" * 70)
    print("דוגמה 4: שיפור שיר עם בדיקה נכונה")
    print("=" * 70)
    
    result = improve_poem_correct(poem, pattern='ABBA')
    
    print("\nשיר מקורי:")
    for i, line in enumerate(result['original_lines'], 1):
        print(f"  {i}. {line}")
    
    print(f"\nתבנית: {result['pattern']}")
    print(f"בעיות: {result['num_issues_before']}")
    
    print("\nבעיות לפי סיומת פונטית:")
    for issue in result['issues_before']:
        print(f"  קבוצה {issue['group']}: שורות {issue['line_numbers']}")
        print(f"    מילים: {issue['words']}")
        print(f"    סיומת 1: {issue['suffix1']}")
        print(f"    סיומת 2: {issue['suffix2']}")
        print(f"    רמה: {issue['level']}")
        print(f"    הסבר: {issue['explanation']}")
    
    print("\nשיר משופר:")
    for i, line in enumerate(result['improved_lines'], 1):
        print(f"  {i}. {line}")
    
    print(f"\nבעיות לאחר שיפור: {result['num_issues_after']}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("דוגמאות - בדיקת סיומת פונטית נכונה")
    print("=" * 70)
    
    try:
        example_1_phonetic_suffix()
    except Exception as e:
        print(f"שגיאה בדוגמה 1: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_2_correct_rhyme()
    except Exception as e:
        print(f"שגיאה בדוגמה 2: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_3_wrong_rhyme()
    except Exception as e:
        print(f"שגיאה בדוגמה 3: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_4_improve_poem()
    except Exception as e:
        print(f"שגיאה בדוגמה 4: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("סיום דוגמאות")
    print("=" * 70)
