"""
אינטגרציה - שילוב השירות המשופר עם המערכת הקיימת.
"""
from services.improved_suggestion_service import (
    improve_poem_rhyme,
    get_suggestions_by_rhyme,
    get_best_suggestion,
    vocalize_lines,
)
from core.rhyme_checker import RhymeChecker


class PoemImprover:
    """
    מחלקה לשיפור חריזה בשיר.
    
    שימוש:
    1. טען שיר
    2. בדוק בעיות חריזה
    3. קבל הצעות
    4. בחר הצעות
    5. שפר את השיר
    """
    
    def __init__(self, lines: list[str]):
        """אתחל עם שיר."""
        self.original_lines = lines
        self.current_lines = lines.copy()
        self.metadata = vocalize_lines(lines)
        self.analysis = improve_poem_rhyme(lines)
    
    def get_issues(self) -> list[dict]:
        """קבל רשימת בעיות חריזה."""
        return self.analysis['issues']
    
    def get_suggestions_for_line(self, line_idx: int) -> list[tuple[str, int]]:
        """קבל הצעות לשורה מסוימת."""
        if line_idx >= len(self.current_lines):
            return []
        
        # קבל מפתחות חרוז של שורות אחרות
        rhyme_keys = []
        for meta in self.metadata:
            key = RhymeChecker.extract_rhyme_key(
                meta['last_word_vocalized'],
                meta['stress_type']
            )
            rhyme_keys.append(key)
        
        # קבל הצעות לפי כל מפתח חרוז אחר
        all_suggestions = {}
        for other_idx, other_key in enumerate(rhyme_keys):
            if other_idx == line_idx:
                continue
            
            suggestions = get_suggestions_by_rhyme(
                self.current_lines,
                line_idx,
                self.metadata[line_idx]['original_word'],
                other_key,
                5,
                set()
            )
            
            for word, level in suggestions:
                if word not in all_suggestions:
                    all_suggestions[word] = level
                else:
                    all_suggestions[word] = min(all_suggestions[word], level)
        
        # מיין לפי רמה
        sorted_suggestions = sorted(all_suggestions.items(), key=lambda x: x[1])
        return sorted_suggestions[:10]
    
    def apply_suggestion(self, line_idx: int, word: str) -> str:
        """החל הצעה לשורה."""
        if line_idx >= len(self.current_lines):
            return self.current_lines[line_idx]
        
        words = self.current_lines[line_idx].split()
        if words:
            words[-1] = word
            self.current_lines[line_idx] = ' '.join(words)
            
            # עדכן מטא-דאטה
            self.metadata = vocalize_lines(self.current_lines)
            self.analysis = improve_poem_rhyme(self.current_lines)
        
        return self.current_lines[line_idx]
    
    def get_status(self) -> dict:
        """קבל סטטוס של השיר."""
        return {
            'original_lines': self.original_lines,
            'current_lines': self.current_lines,
            'issues': self.analysis['issues'],
            'num_issues': self.analysis['num_issues'],
            'is_complete': self.analysis['num_issues'] == 0,
        }
    
    def auto_improve(self) -> dict:
        """שפר את השיר אוטומטית."""
        for line_idx, suggestions in self.analysis['suggestions'].items():
            if suggestions:
                best_word = suggestions[0][0]
                self.apply_suggestion(line_idx, best_word)
        
        return self.get_status()


def improve_poem(lines: list[str]) -> dict:
    """
    שפר את חריזת השיר בצורה אוטומטית.
    
    Args:
        lines: רשימת שורות של השיר
    
    Returns:
        dict עם:
        - original_lines: השורות המקוריות
        - improved_lines: השורות המשופרות
        - issues_before: בעיות לפני
        - issues_after: בעיות אחרי
        - changes: רשימת השינויים
    """
    improver = PoemImprover(lines)
    
    # קבל בעיות לפני
    issues_before = improver.get_issues()
    
    # שפר אוטומטית
    status = improver.auto_improve()
    
    # קבל בעיות אחרי
    issues_after = status['issues']
    
    # חשב שינויים
    changes = []
    for i, (orig, improved) in enumerate(zip(lines, status['current_lines'])):
        if orig != improved:
            changes.append({
                'line_idx': i,
                'original': orig,
                'improved': improved,
            })
    
    return {
        'original_lines': lines,
        'improved_lines': status['current_lines'],
        'issues_before': issues_before,
        'issues_after': issues_after,
        'num_issues_before': len(issues_before),
        'num_issues_after': len(issues_after),
        'changes': changes,
        'is_complete': status['is_complete'],
    }


def interactive_improve_poem(lines: list[str]) -> dict:
    """
    שפר את השיר בצורה אינטראקטיבית.
    
    זרימה:
    1. טען שיר
    2. הצג בעיות
    3. לכל בעיה - הצג הצעות
    4. המשתמש בוחר הצעה
    5. החל הצעה
    6. חזור לשלב 2
    """
    improver = PoemImprover(lines)
    
    print("=" * 60)
    print("שיפור חריזה אינטראקטיבי")
    print("=" * 60)
    
    print("\nשיר מקורי:")
    for i, line in enumerate(improver.original_lines, 1):
        print(f"{i}. {line}")
    
    iteration = 0
    while improver.get_issues():
        iteration += 1
        print(f"\n--- איטרציה {iteration} ---")
        
        issues = improver.get_issues()
        print(f"בעיות חריזה: {len(issues)}")
        
        for issue in issues[:1]:  # טפל בבעיה אחת בכל פעם
            line_idx = issue['lines'][0] - 1
            print(f"\nשורה {line_idx + 1}: {improver.current_lines[line_idx]}")
            
            suggestions = improver.get_suggestions_for_line(line_idx)
            if suggestions:
                best_word = suggestions[0][0]
                print(f"הצעה הטובה ביותר: {best_word}")
                improver.apply_suggestion(line_idx, best_word)
                print(f"שורה משופרת: {improver.current_lines[line_idx]}")
        
        if iteration > 10:  # הגבל את מספר האיטרציות
            break
    
    status = improver.get_status()
    
    print("\n" + "=" * 60)
    print("שיר משופר:")
    print("=" * 60)
    for i, line in enumerate(status['current_lines'], 1):
        print(f"{i}. {line}")
    
    print(f"\nבעיות נותרות: {status['num_issues']}")
    print(f"שיר שלם: {status['is_complete']}")
    
    return status
