"""
דוגמאות - שיפור שורות שלמות.
"""

def example_1():
    """דוגמה 1: שיפור שורות שלמות."""
    from advanced_poem_improver import improve_poem_advanced
    
    poem = ["הלב שלי קטו", "בעולם הזה", "אני שר", "בלילה"]
    
    print("=" * 70)
    print("שיפור שורות שלמות (לא רק מילה אחרונה)")
    print("=" * 70)
    
    print("\nשיר מקורי:")
    for i, line in enumerate(poem, 1):
        print(f"  {i}. {line}")
    
    result = improve_poem_advanced(poem, pattern='ABBA', method='smart')
    
    print("\nשיר משופר:")
    for i, line in enumerate(result['improved_lines'], 1):
        print(f"  {i}. {line}")
    
    print(f"\nשינויים: {result['num_changes']}")
    for change in result['changes']:
        print(f"  שורה {change['line_number']}: '{change['original']}' → '{change['improved']}'")


if __name__ == "__main__":
    example_1()
