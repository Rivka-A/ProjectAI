"""
דוגמה עובדת - שיפור חריזה בשיר.
"""

def example_improve_poem():
    """דוגמה: שפר את חריזת השיר."""
    from services.improved_suggestion_service import improve_poem_rhyme
    
    # שיר עם בעיות חריזה
    poem = [
        "הלב שלי קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("=" * 60)
    print("שיר מקורי:")
    print("=" * 60)
    for i, line in enumerate(poem, 1):
        print(f"{i}. {line}")
    
    # שפר את החריזה
    print("\n" + "=" * 60)
    print("ניתוח חריזה:")
    print("=" * 60)
    
    result = improve_poem_rhyme(poem)
    
    print(f"\nבעיות חריזה: {result['num_issues']}")
    for issue in result['issues']:
        lines_nums = issue['lines']
        words = issue['words']
        level = issue['level']
        print(f"  שורות {lines_nums[0]}-{lines_nums[1]}: '{words[0]}' ו'{words[1]}' (רמה {level})")
    
    # הצעות
    print("\n" + "=" * 60)
    print("הצעות לשיפור:")
    print("=" * 60)
    
    for line_idx, suggestions in result['suggestions'].items():
        if suggestions:
            print(f"\nשורה {line_idx + 1} ('{result['metadata'][line_idx]['original_word']}'):")
            for i, (word, level) in enumerate(suggestions[:3], 1):
                level_name = {
                    1: "חרוז מושלם",
                    2: "חרוז טוב",
                    3: "עיצור משותף",
                    4: "תנועה משותפת",
                    5: "אין חרוז",
                }.get(level, "לא ידוע")
                print(f"  {i}. {word} (רמה {level}: {level_name})")


def example_get_best_suggestion():
    """דוגמה: קבל את ההצעה הטובה ביותר."""
    from services.improved_suggestion_service import get_best_suggestion, vocalize_lines
    from core.rhyme_checker import RhymeChecker
    
    lines = ["הלב קטו", "בעולם הזה"]
    metadata = vocalize_lines(lines)
    
    # קבל מפתח חרוז לשורה השנייה
    target_key = RhymeChecker.extract_rhyme_key(
        metadata[1]['last_word_vocalized'],
        metadata[1]['stress_type']
    )
    
    # קבל את ההצעה הטובה ביותר לשורה הראשונה
    best = get_best_suggestion(lines, 0, metadata[0]['original_word'], target_key)
    
    print("=" * 60)
    print("ההצעה הטובה ביותר:")
    print("=" * 60)
    print(f"שורה מקורית: {lines[0]}")
    print(f"מילה מקורית: {metadata[0]['original_word']}")
    print(f"מילה מוצעת: {best}")
    print(f"שורה משופרת: {lines[0].replace(metadata[0]['original_word'], best)}")


def example_get_suggestions_by_rhyme():
    """דוגמה: קבל הצעות מסוננות לפי חריזה."""
    from services.improved_suggestion_service import get_suggestions_by_rhyme, vocalize_lines
    from core.rhyme_checker import RhymeChecker
    
    lines = ["הלב קטו", "בעולם הזה"]
    metadata = vocalize_lines(lines)
    
    # קבל מפתח חרוז לשורה השנייה
    target_key = RhymeChecker.extract_rhyme_key(
        metadata[1]['last_word_vocalized'],
        metadata[1]['stress_type']
    )
    
    # קבל הצעות לשורה הראשונה
    suggestions = get_suggestions_by_rhyme(
        lines, 0, metadata[0]['original_word'], target_key, 5, set()
    )
    
    print("=" * 60)
    print("הצעות מסוננות לפי חריזה:")
    print("=" * 60)
    print(f"שורה: {lines[0]}")
    print(f"מילה: {metadata[0]['original_word']}")
    print(f"יעד חרוז: {metadata[1]['original_word']}")
    print(f"\nהצעות (מדורגות):")
    
    for i, (word, level) in enumerate(suggestions, 1):
        level_name = {
            1: "חרוז מושלם",
            2: "חרוז טוב",
            3: "עיצור משותף",
            4: "תנועה משותפת",
            5: "אין חרוז",
        }.get(level, "לא ידוע")
        print(f"  {i}. {word} (רמה {level}: {level_name})")


def example_complete_workflow():
    """דוגמה: זרימת עבודה שלמה."""
    from services.improved_suggestion_service import improve_poem_rhyme
    
    # שיר עם בעיות חריזה
    poem = [
        "הלב שלי קטו",
        "בעולם הזה",
        "אני שר",
        "בלילה"
    ]
    
    print("=" * 60)
    print("זרימת עבודה שלמה:")
    print("=" * 60)
    
    # שלב 1: ניתוח
    print("\nשלב 1: ניתוח השיר")
    result = improve_poem_rhyme(poem)
    print(f"בעיות חריזה: {result['num_issues']}")
    
    # שלב 2: הצעות
    print("\nשלב 2: קבלת הצעות")
    for line_idx, suggestions in result['suggestions'].items():
        if suggestions:
            best_word = suggestions[0][0]
            print(f"שורה {line_idx + 1}: {poem[line_idx]}")
            print(f"  → {poem[line_idx].replace(result['metadata'][line_idx]['original_word'], best_word)}")
    
    # שלב 3: שיפור
    print("\nשלב 3: שיפור השיר")
    improved_poem = poem.copy()
    for line_idx, suggestions in result['suggestions'].items():
        if suggestions:
            best_word = suggestions[0][0]
            words = improved_poem[line_idx].split()
            words[-1] = best_word
            improved_poem[line_idx] = ' '.join(words)
    
    print("שיר משופר:")
    for i, line in enumerate(improved_poem, 1):
        print(f"{i}. {line}")
    
    # שלב 4: בדיקה
    print("\nשלב 4: בדיקה של השיר המשופר")
    final_result = improve_poem_rhyme(improved_poem)
    print(f"בעיות חריזה נותרות: {final_result['num_issues']}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("דוגמאות - שיפור חריזה בשיר")
    print("=" * 60 + "\n")
    
    try:
        example_improve_poem()
    except Exception as e:
        print(f"שגיאה בדוגמה 1: {e}\n")
    
    try:
        print("\n")
        example_get_suggestions_by_rhyme()
    except Exception as e:
        print(f"שגיאה בדוגמה 2: {e}\n")
    
    try:
        print("\n")
        example_get_best_suggestion()
    except Exception as e:
        print(f"שגיאה בדוגמה 3: {e}\n")
    
    try:
        print("\n")
        example_complete_workflow()
    except Exception as e:
        print(f"שגיאה בדוגמה 4: {e}\n")
    
    print("\n" + "=" * 60)
    print("סיום דוגמאות")
    print("=" * 60)
