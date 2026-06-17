from core.stress_detector import StressDetector

def main():
    print("=== בדיקת מקרים מיוחדים מורחבת (כולל הצלחה, ברכה, שמחה) ===")
    
    test_words = [
        # מלעיל עברי מיוחד (הטעמה לפני הסוף)
        {"original": "אלה", "vocalized": "אֵלֶּה", "expected": "מלעיל"},
        {"original": "לילה", "vocalized": "לַיְלָה", "expected": "מלעיל"},
        {"original": "ביתה", "vocalized": "בַּיְתָה", "expected": "מלעיל"},
        
        # מלרע עברי (הטעמה בסוף - המילים החדשות שלך!)
        {"original": "הצלחה", "vocalized": "הַצְלָחָה", "expected": "מלרע"},
        {"original": "ברכה", "vocalized": "בְּרָכָה", "expected": "מלרע"},
        {"original": "שמחה", "vocalized": "שִׂמְחָה", "expected": "מלרע"},
        {"original": "רוצה", "vocalized": "רוֹצֶה", "expected": "מלרע"},
        {"original": "הלכה", "vocalized": "הָלְכָה", "expected": "מלרע"},
        
        # מילים לועזיות (מלעיל)
        {"original": "סטטוס", "vocalized": "סְטָטוּס", "expected": "מלעיל"},
        {"original": "אוטובוס", "vocalized": "אוֹטוֹבּוּס", "expected": "מלעיל"}
    ]
    
    print(f"{'מילה':<10} | {'מנוקד':<12} | {'זיהוי מערכת':<12} | {'סטטוס'}")
    print("-" * 55)
    
    for word in test_words:
        detected_stress = StressDetector.detect_stress(word["vocalized"])
        status = "✅ הצלחה" if detected_stress == word["expected"] else "❌ שגיאה"
        print(f"{word['original']:<10} | {word['vocalized']:<11} | {detected_stress:<11} | {status}")

if __name__ == "__main__":
    main()