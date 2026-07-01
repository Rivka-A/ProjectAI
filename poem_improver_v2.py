"""
משפר חריזה - עם תמיכה ב-ABBA וזיהוי מילים עם ניקוד שונה.
"""
from services.improved_suggestion_service import (
    improve_poem_rhyme,
    get_suggestions_by_rhyme,
    get_best_suggestion,
    vocalize_lines,
)
from services.rhyme_analyzer import detect_rhyme_pattern, _is_rhyme, extract_rhyme_key_normalized
from core.rhyme_checker import RhymeChecker


class PoemImprover:
    """
    מחלקה לשיפור חריזה בשיר עם תמיכה ב-ABBA.
    """
    
    def __init__(self, lines: list[str], pattern: str = None):
        """
        אתחל עם שיר.
        
        Args:
            lines: רשימת שורות
            pattern: תבנית חריזה רצויה (AABB, ABAB, ABBA)
        """
        self.original_lines = lines
        self.current_lines = lines.copy()
        self.metadata = vocalize_lines(lines)
        
        # זהה תבנית אוטומטית אם לא צוינה
        if pattern:
            self.target_pattern = pattern
        else:
            detected = detect_rhyme_pattern(lines)
            self.target_pattern = detected['pattern']
        
        # חשב מפתחות חרוז מנורמלים
        self.rhyme_keys = self._compute_rhyme_keys()
    
    def _compute_rhyme_keys(self) -> list:
        """חשב מפתחות חרוז מנורמלים לכל שורה."""
        keys = []
        for meta in self.metadata:
            key = extract_rhyme_key_normalized(meta['last_word_vocalized'])
            keys.append(key)
        return keys
    
    def get_rhyme_groups(self) -> dict:
        """
        קבל את קבוצות החריזה לפי התבנית הנבחרת.
        
        Returns:
            dict עם קבוצות חריזה:
            {
                'A': [0, 3],  # שורות שצריכות להתחרז ב-A
                'B': [1, 2],  # שורות שצריכות להתחרז ב-B
                ...
            }
        """
        if self.target_pattern == 'ABBA':
            return {
                'A': [0, 3],  # שורות 1 ו-4
                'B': [1, 2],  # שורות 2 ו-3
            }
        elif self.target_pattern == 'AABB':
            return {
                'A': [0, 1],  # שורות 1 ו-2
                'B': [2, 3],  # שורות 3 ו-4
            }
        elif self.target_pattern == 'ABAB':
            return {
                'A': [0, 2],  # שורות 1 ו-3
                'B': [1, 3],  # שורות 2 ו-4
            }
        else:
            # חופשית - זוגות עוקבים
            return {
                'A': [0, 1],
                'B': [2, 3],
            }
    
    def get_issues(self) -> list:
        """
        קבל רשימת בעיות חריזה.
        
        Returns:
            list של בעיות:
            [{
                'group': 'A',
                'lines': [0, 3],
                'words': ['קטו', 'לילה'],
                'level': 5,
                'needs_fix': True
            }, ...]
        """
        issues = []
        groups = self.get_rhyme_groups()
        
        for group_name, line_indices in groups.items():
            if len(line_indices) != 2:
                continue
            
            idx1, idx2 = line_indices
            
            # בדוק אם המילים מתחרזות
            key1 = self.rhyme_keys[idx1]
            key2 = self.rhyme_keys[idx2]
            
            level = RhymeChecker.rhyme_level(key1, key2)
            needs_fix = level > 2
            
            issues.append({
                'group': group_name,
                'lines': line_indices,
                'line_numbers': [idx1 + 1, idx2 + 1],  # 1-based
                'words': [
                    self.metadata[idx1]['original_word'],
                    self.metadata[idx2]['original_word']
                ],
                'level': level,
                'needs_fix': needs_fix,
            })
        
        return issues
    
    def get_suggestions_for_line(self, line_idx: int) -> list:
        """
        קבל הצעות לשורה מסוימת בהתאם לתבנית החריזה.
        
        Args:
            line_idx: אינדקס השורה (0-based)
        
        Returns:
            list של (מילה, רמת_חרוז)
        """
        if line_idx >= len(self.current_lines):
            return []
        
        # מצא את הקבוצה של השורה
        groups = self.get_rhyme_groups()
        target_group = None
        partner_idx = None
        
        for group_name, line_indices in groups.items():
            if line_idx in line_indices:
                target_group = group_name
                partner_idx = line_indices[0] if line_indices[1] == line_idx else line_indices[1]
                break
        
        if partner_idx is None:
            return []
        
        # קבל מפתח חרוז של השורה השותפה
        target_key = self.rhyme_keys[partner_idx]
        
        # קבל הצעות
        suggestions = get_suggestions_by_rhyme(
            self.current_lines,
            line_idx,
            self.metadata[line_idx]['original_word'],
            target_key,
            5,
            set()
        )
        
        return suggestions
    
    def apply_suggestion(self, line_idx: int, word: str) -> str:
        """החל הצעה לשורה."""
        if line_idx >= len(self.current_lines):
            return self.current_lines[line_idx]
        
        words = self.current_lines[line_idx].split()
        if words:
            words[-1] = word
            self.current_lines[line_idx] = ' '.join(words)
            
            # עדכן מטא-דאטה ומפתחות חרוז
            self.metadata = vocalize_lines(self.current_lines)
            self.rhyme_keys = self._compute_rhyme_keys()
        
        return self.current_lines[line_idx]
    
    def get_status(self) -> dict:
        """קבל סטטוס של השיר."""
        issues = self.get_issues()
        num_issues = sum(1 for issue in issues if issue['needs_fix'])
        
        return {
            'original_lines': self.original_lines,
            'current_lines': self.current_lines,
            'pattern': self.target_pattern,
            'issues': issues,
            'num_issues': num_issues,
            'is_complete': num_issues == 0,
        }
    
    def auto_improve(self) -> dict:
        """שפר את השיר אוטומטית."""
        # קבל בעיות
        issues = self.get_issues()
        
        # טפל בכל בעיה
        for issue in issues:
            if not issue['needs_fix']:
                continue
            
            line_indices = issue['lines']
            
            # בחר את השורה עם הפחות השפעה
            for line_idx in line_indices:
                suggestions = self.get_suggestions_for_line(line_idx)
                if suggestions:
                    best_word = suggestions[0][0]
                    self.apply_suggestion(line_idx, best_word)
                    break
        
        return self.get_status()


def improve_poem_with_pattern(lines: list[str], pattern: str = None) -> dict:
    """
    שפר את חריזת השיר עם תבנית מוגדרת.
    
    Args:
        lines: רשימת שורות
        pattern: תבנית רצויה (AABB, ABAB, ABBA)
    
    Returns:
        dict עם תוצאות
    """
    improver = PoemImprover(lines, pattern)
    
    # קבל בעיות לפני
    issues_before = improver.get_issues()
    
    # שפר
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
        'pattern': status['pattern'],
        'issues_before': issues_before,
        'issues_after': issues_after,
        'num_issues_before': sum(1 for issue in issues_before if issue['needs_fix']),
        'num_issues_after': sum(1 for issue in issues_after if issue['needs_fix']),
        'changes': changes,
        'is_complete': status['is_complete'],
    }
