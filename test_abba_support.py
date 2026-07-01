"""
דוגמאות - תמיכה ב-ABBA וזיהוי מילים עם ניקוד שונה.
"""


def example_1_abba_pattern():
    """דוגמה 1: שיפור שיר עם תבנית ABBA."""
    from poem_improver_v2 import PoemImprover
    
    poem = [
        "הלב שלי קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("=" * 70)
    print("דוגמה 1: תבנית ABBA")
    print("=" * 70)
    
    improver = PoemImprover(poem, pattern='ABBA')
    
    print("\nשיר מקורי:")
    for i, line in enumerate(poem, 1):
        print(f"  {i}. {line}")
    
    print(f"\nתבנית יעד: {improver.target_pattern}")
    
    # קבל קבוצות חריזה
    groups = improver.get_rhyme_groups()
    print("\nקבוצות חריזה:")
    for group, indices in groups.items():
        line_nums = [i + 1 for i in indices]
        print(f"  {group}: שורות {line_nums}")
    
    # קבל בעיות
    print("\nבעיות חריזה:")
    for issue in improver.get_issues():
        if issue['needs_fix']:
            print(f"  קבוצה {issue['group']}: שורות {issue['line_numbers']}")
            print(f"    מילים: {issue['words']}")
            print(f"    רמה: {issue['level']}")
    
    # שפר
    status = improver.auto_improve()
    
    print("\nשיר משופר:")
    for i, line in enumerate(status['current_lines'], 1):
        print(f"  {i}. {line}")
    
    print(f"\nבעיות נותרות: {status['num_issues']}")
    print(f"שיר שלם: {status['is_complete']}")


def example_2_different_patterns():
    """דוגמה 2: השוואת תבניות שונות."""
    from poem_improver_v2 import improve_poem_with_pattern
    
    poem = [
        "הלב קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("\n" + "=" * 70)
    print("דוגמה 2: השוואת תבניות")
    print("=" * 70)
    
    patterns = ['AABB', 'ABAB', 'ABBA']
    
    for pattern in patterns:
        print(f"\n--- תבנית {pattern} ---")
        result = improve_poem_with_pattern(poem, pattern=pattern)
        
        print(f"בעיות: {result['num_issues_before']} → {result['num_issues_after']}")
        print(f"שינויים: {len(result['changes'])}")
        
        if result['changes']:
            print("שיר משופר:")
            for i, line in enumerate(result['improved_lines'], 1):
                print(f"  {i}. {line}")


def example_3_normalized_rhyme():
    """דוגמה 3: זיהוי מילים עם ניקוד שונה."""
    from services.rhyme_analyzer import extract_rhyme_key_normalized
    from core.rhyme_checker import RhymeChecker
    
    print("\n" + "=" * 70)
    print("דוגמה 3: זיהוי מילים עם ניקוד שונה")
    print("=" * 70)
    
    # מילים עם קמץ vs פתח
    word1 = "קָטוּעַ"  # קמץ
    word2 = "קַטוּעַ"  # פתח
    
    print(f"\nמילה 1: {word1} (עם קמץ)")
    print(f"מילה 2: {word2} (עם פתח)")
    
    # חלץ מפתחות רגילים
    key1_regular = RhymeChecker.extract_rhyme_key(word1, "מלרע")
    key2_regular = RhymeChecker.extract_rhyme_key(word2, "מלרע")
    
    print(f"\nמפתחות רגילים:")
    print(f"  מילה 1: {key1_regular}")
    print(f"  מילה 2: {key2_regular}")
    print(f"  זהים? {key1_regular == key2_regular}")
    
    # חלץ מפתחות מנורמלים
    key1_norm = extract_rhyme_key_normalized(word1)
    key2_norm = extract_rhyme_key_normalized(word2)
    
    print(f"\nמפתחות מנורמלים:")
    print(f"  מילה 1: {key1_norm}")
    print(f"  מילה 2: {key2_norm}")
    print(f"  זהים? {key1_norm == key2_norm}")
    
    # בדוק חריזה
    level_regular = RhymeChecker.rhyme_level(key1_regular, key2_regular)
    level_norm = RhymeChecker.rhyme_level(key1_norm, key2_norm)
    
    print(f"\nרמת חרוז (רגיל): {level_regular}")
    print(f"רמת חרוז (מנורמל): {level_norm}")
    
    if key1_norm == key2_norm:
        print("\n✓ המילים זוהו כזהות לאחר נרמול!")


def example_4_complete_workflow():
    """דוגמה 4: זרימת עבודה שלמה עם ABBA."""
    from poem_improver_v2 import improve_poem_with_pattern
    
    poem = [
        "הלב שלי קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("\n" + "=" * 70)
    print("דוגמה 4: זרימת עבודה שלמה עם ABBA")
    print("=" * 70)
    
    print("\nשלב 1: שיר מקורי")
    for i, line in enumerate(poem, 1):
        print(f"  {i}. {line}")
    
    print("\nשלב 2: שפר עם תבנית ABBA")
    result = improve_poem_with_pattern(poem, pattern='ABBA')
    
    print(f"תבנית: {result['pattern']}")
    print(f"בעיות לפני: {result['num_issues_before']}")
    print(f"בעיות אחרי: {result['num_issues_after']}")
    
    print("\nשלב 3: שיר משופר")
    for i, line in enumerate(result['improved_lines'], 1):
        print(f"  {i}. {line}")
    
    print("\nשלב 4: סיכום")
    print(f"  שינויים: {len(result['changes'])}")
    print(f"  שיפור: {result['num_issues_before']} → {result['num_issues_after']} בעיות")
    print(f"  שיר שלם: {result['is_complete']}")


def example_5_interactive_selection():
    """דוגמה 5: בחירת הצעות ידנית עם ABBA."""
    from poem_improver_v2 import PoemImprover
    
    poem = [
        "הלב קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("\n" + "=" * 70)
    print("דוגמה 5: בחירת הצעות ידנית")
    print("=" * 70)
    
    improver = PoemImprover(poem, pattern='ABBA')
    
    print("\nשיר:")
    for i, line in enumerate(poem, 1):
        print(f"  {i}. {line}")
    
    print("\nבעיות:")
    for issue in improver.get_issues():
        if issue['needs_fix']:
            print(f"  קבוצה {issue['group']}: שורות {issue['line_numbers']}")
    
    # קבל הצעות לשורה ראשונה (קבוצה A)
    print("\nהצעות לשורה 1 (קבוצה A):")
    suggestions = improver.get_suggestions_for_line(0)
    for i, (word, level) in enumerate(suggestions[:3], 1):
        level_name = {1: "מושלם", 2: "טוב", 3: "עיצור", 4: "תנועה", 5: "אין"}.get(level, "?")
        print(f"  {i}. {word} (רמה {level}: {level_name})")
    
    # בחר הצעה
    if suggestions:
        best_word = suggestions[0][0]
        print(f"\nבחירה: {best_word}")
        improver.apply_suggestion(0, best_word)
        
        print("\nשיר לאחר תיקון:")
        for i, line in enumerate(improver.current_lines, 1):
            print(f"  {i}. {line}")
    
    # בדוק סטטוס
    status = improver.get_status()
    print(f"\nבעיות נותרות: {status['num_issues']}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("דוגמאות - ABBA וזיהוי מילים עם ניקוד שונה")
    print("=" * 70)
    
    try:
        example_1_abba_pattern()
    except Exception as e:
        print(f"שגיאה בדוגמה 1: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_2_different_patterns()
    except Exception as e:
        print(f"שגיאה בדוגמה 2: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_3_normalized_rhyme()
    except Exception as e:
        print(f"שגיאה בדוגמה 3: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_4_complete_workflow()
    except Exception as e:
        print(f"שגיאה בדוגמה 4: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_5_interactive_selection()
    except Exception as e:
        print(f"שגיאה בדוגמה 5: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("סיום דוגמאות")
    print("=" * 70)
