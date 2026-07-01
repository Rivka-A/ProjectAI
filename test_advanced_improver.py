"""
דוגמאות - שיפור שורות שלמות (לא רק מילה אחרונה).
"""


def example_1_line_variations():
    """דוגמה 1: וריאציות שונות לשורה."""
    from services.line_generator import suggest_line_variations
    
    line = "הלב שלי קטו"
    
    # סיומת פונטית רצויה (למשל: חולם + ר"י)
    target_suffix = ('O', ('r',))
    
    print("=" * 70)
    print("דוגמה 1: וריאציות לשורה")
    print("=" * 70)
    
    print(f"\nשורה מקורית: {line}")
    print(f"סיומת רצויה: {target_suffix} (חולם + ר'י)")
    
    # קבל וריאציות
    result = suggest_line_variations(line, target_suffix, variation_type='all')
    
    print(f"\nמצאתי {len(result['variations'])} וריאציות:")
    
    for i, var in enumerate(result['variations'][:5], 1):
        print(f"\n{i}. {var['line']}")
        print(f"   שיטה: {var['method']}")
        print(f"   רמה: {var['level']}, איכות: {var['quality']}")


def example_2_replace_last_word():
    """דוגמה 2: החלפת מילה אחרונה בלבד."""
    from services.line_generator import rewrite_line_for_rhyme
    
    line = "הלב שלי קטו"
    target_suffix = ('A', ())  # פתח בלי עיצור
    
    print("\n" + "=" * 70)
    print("דוגמה 2: החלפת מילה אחרונה")
    print("=" * 70)
    
    print(f"\nשורה מקורית: {line}")
    print(f"סיומת רצויה: {target_suffix}")
    
    suggestions = rewrite_line_for_rhyme(
        line,
        target_suffix,
        preserve_meaning=True,
        num_suggestions=10
    )
    
    print(f"\nהצעות (החלפת מילה אחרונה):")
    for i, sug in enumerate(suggestions[:5], 1):
        print(f"{i}. {sug['line']}")
        print(f"   רמה: {sug['level']}, איכות: {sug['quality']}")


def example_3_extend_line():
    """דוגמה 3: הוספת מילים לשורה."""
    from services.line_generator import _extend_line
    
    line = "הלב שלי"
    target_suffix = ('U', ('r',))  # שורוק + ר'י
    
    print("\n" + "=" * 70)
    print("דוגמה 3: הוספת מילים")
    print("=" * 70)
    
    print(f"\nשורה מקורית: {line}")
    print(f"סיומת רצויה: {target_suffix}")
    
    suggestions = _extend_line(line, target_suffix, 10)
    
    print(f"\nהצעות (הוספת מילים):")
    for i, sug in enumerate(suggestions[:5], 1):
        print(f"{i}. {sug['line']}")
        print(f"   רמה: {sug['level']}")


def example_4_advanced_improver():
    """דוגמה 4: שיפור מתקדם של שיר."""
    from advanced_poem_improver import improve_poem_advanced
    
    poem = [
        "הלב שלי קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("\n" + "=" * 70)
    print("דוגמה 4: שיפור מתקדם")
    print("=" * 70)
    
    print("\nשיר מקורי:")
    for i, line in enumerate(poem, 1):
        print(f"  {i}. {line}")
    
    # שיטה 1: רק החלפת מילה אחרונה
    print("\n--- שיטה 1: החלפת מילה אחרונה ---")
    result1 = improve_poem_advanced(poem, pattern='ABBA', method='last_word_only')
    
    print("שיר משופר:")
    for i, line in enumerate(result1['improved_lines'], 1):
        print(f"  {i}. {line}")
    
    print(f"שינויים: {result1['num_changes']}")
    
    # שיטה 2: חכם (כל השיטות)
    print("\n--- שיטה 2: חכם (כל השיטות) ---")
    result2 = improve_poem_advanced(poem, pattern='ABBA', method='smart')
    
    print("שיר משופר:")
    for i, line in enumerate(result2['improved_lines'], 1):
        print(f"  {i}. {line}")
    
    print(f"שינויים: {result2['num_changes']}")
    
    if result2['changes']:
        print("\nפרטי שינויים:")
        for change in result2['changes']:
            print(f"  שורה {change['line_number']}:")
            print(f"    לפני: {change['original']}")
            print(f"    אחרי: {change['improved']}")
            print(f"    שיטה: {change['method']}")


def example_5_interactive():
    """דוגמה 5: שיפור אינטראקטיבי."""
    from advanced_poem_improver import AdvancedPoemImprover
    
    poem = [
        "הלב שלי קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("\n" + "=" * 70)
    print("דוגמה 5: שיפור אינטראקטיבי")
    print("=" * 70)
    
    improver = AdvancedPoemImprover(poem, pattern='ABBA')
    
    print("\nשיר:")
    for i, line in enumerate(poem, 1):
        print(f"  {i}. {line}")
    
    # קבל בעיות
    print("\nבעיות:")
    for issue in improver.get_issues():
        if issue['needs_fix']:
            print(f"  קבוצה {issue['group']}: שורות {issue['line_numbers']}")
            print(f"    רמה: {issue['level']}")
    
    # קבל הצעות לשורה 1
    print("\nהצעות לשורה 1:")
    suggestions = improver.get_line_suggestions(0, variation_type='all')
    
    if suggestions:
        for i, sug in enumerate(suggestions[:5], 1):
            print(f"  {i}. {sug['line']}")
            print(f"     שיטה: {sug['method']}, רמה: {sug['level']}, איכות: {sug['quality']}")
        
        # בחר את ההצעה הראשונה
        best = suggestions[0]
        print(f"\nבחירה: {best['line']}")
        improver.apply_line_suggestion(0, best['line'])
    
    # בדוק סטטוס
    status = improver.get_status()
    print(f"\nבעיות נותרות: {status['num_issues']}")
    
    print("\nשיר נוכחי:")
    for i, line in enumerate(status['current_lines'], 1):
        print(f"  {i}. {line}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("דוגמאות - שיפור שורות שלמות")
    print("=" * 70)
    
    try:
        example_1_line_variations()
    except Exception as e:
        print(f"שגיאה: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_2_replace_last_word()
    except Exception as e:
        print(f"שגיאה: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_3_extend_line()
    except Exception as e:
        print(f"שגיאה: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_4_advanced_improver()
    except Exception as e:
        print(f"שגיאה: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        example_5_interactive()
    except Exception as e:
        print(f"שגיאה: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("סיום")
    print("=" * 70)
