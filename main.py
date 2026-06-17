from services.nakdan_service import NakdanService
from core.stress_detector import StressDetector

def main():
    print("--- מערכת ניתוח חריזה ושירה ---")
    
    # 1. אתחול השירות
    nakdan = NakdanService()
    
    # 2. טקסט לבדיקה
    sample_text = "הילד כותב במחברת שלו"
    print(f"שולח לניקוד: '{sample_text}'")
    
    # 3. קריאה ל-API
    result = nakdan.get_vocalized_text(sample_text)
    
    if result:
        print("\nתוצאות הניתוח:")
        for item in result:
            # דילוג על רווחים וסימני פיסוק
            if item.get("sep"):
                continue
                
            word = item.get("word")
            options = item.get("options", [])
            
            if options:
                # לקיחת אופציית הניקוד הראשונה שהשרת מציע
                vocalized = options[0]
                
                # הפעלת מנגנון זיהוי ההטעמה
                stress = StressDetector.detect_stress(vocalized)
                print(f"מילה: {word} -> מנוקד: {vocalized} -> הטעמה: {stress}")
    else:
        print("לא התקבלה תשובה מהשרת.")

if __name__ == "__main__":
    main()