# יבוא של המחלקה שלך מהקובץ שבו היא נמצאת
from core.rhyme_checker import RhymeChecker

def test_specific_rhyme():
    # 1. הגדרת המילים המנוקדות כפי שהן מתקבלות מה-API
    word1 = "גִּיתָה"
    word2 = "מִשְׁפָּחָה"
    
    # 2. שליפת סוג ההטעמה (שתיהן מלרע)
    stress = "מלרע"
    
    # 3. הפקת מפתחות החרוז
    key1 = RhymeChecker.extract_rhyme_key(word1, stress)
    key2 = RhymeChecker.extract_rhyme_key(word2, stress)
    
    print(f"--- בדיקת מפתחות חרוז ---")
    print(f"מפתח עבור '{word1}': {key1}")
    print(f"מפתח עבור '{word2}': {key2}")
    
    # 4. בדיקת הציון שמתקבל
    level = RhymeChecker.rhyme_level(key1, key2)
    print(f"\nציון החרוז שהתקבל: {level}")
    
    if level == 1 or level == 2:
        print("❌ באג: האלגוריתם אישר את החרוז כחרוז טוב/מושלם למרות שהעיצורים הנושאים (t ו-x) שונים לחלוטין!")
    else:
        print("✅ האלגוריתם זיהה בצורה נכונה שהחרוז חלש או לא קיים.")

if __name__ == "__main__":
    test_specific_rhyme()