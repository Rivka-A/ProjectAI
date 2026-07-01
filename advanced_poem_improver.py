"""
משפר חריזה מתקדם - יכול לשנות שורות שלמות.
"""
from services.phonetic_rhyme_checker import get_phonetic_suffix, compare_phonetic_suffixes
from services.line_generator import rewrite_line_for_rhyme, suggest_line_variations
from services.improved_suggestion_service import vocalize_lines
from services.rhyme_analyzer import detect_rhyme_pattern
from core.stress_detector import StressDetector


class AdvancedPoemImprover:
    """
    משפר חריזה מתקדם - יכול לשנות שורות שלמות, לא רק מילים אחרונות.
    """
    
    def __init__(self, lines: list, pattern: str = None):
        """אתחל עם שיר ותבנית."""
        self.original_lines = lines
        self.current_lines = lines.copy()
        self.metadata = vocalize_lines(lines)
        
        # זיהוי תבנית
        if pattern:
            self.target_pattern = pattern
        else:
            detected = detect_rhyme_pattern(lines)
            self.target_pattern = detected['pattern']
        
        # חישוב סיומות
        self.phonetic_suffixes = self._compute_suffixes()
    
    def _compute_suffixes(self) -> list:
        """חשב סיומות פונטיות."""
        suffixes = []
        for meta in self.metadata:
            suffix = get_phonetic_suffix(
                meta['last_word_vocalized'],
                meta['stress_type']
            )
            suffixes.append(suffix)
        return suffixes
    
    def get_rhyme_groups(self) -> dict:
        """קבל קבוצות חריזה."""
        if self.target_pattern == 'ABBA':
            return {'A': [0, 3], 'B': [1, 2]}
        elif self.target_pattern == 'AABB':
            return {'A': [0, 1], 'B': [2, 3]}
        elif self.target_pattern == 'ABAB':
            return {'A': [0, 2], 'B': [1, 3]}
        else:
            return {'A': [0, 1], 'B': [2, 3]}
    
    def get_issues(self) -> list:
        """קבל בעיות חריזה."""
        issues = []
        groups = self.get_rhyme_groups()
        
        for group_name, line_indices in groups.items():
            if len(line_indices) != 2:
                continue
            
            idx1, idx2 = line_indices
            
            suffix1 = self.phonetic_suffixes[idx1]
            suffix2 = self.phonetic_suffixes[idx2]
            
            level = compare_phonetic_suffixes(suffix1, suffix2)
            needs_fix = level > 2
            
            issues.append({
                'group': group_name,
                'lines': line_indices,
                'line_numbers': [idx1 + 1, idx2 + 1],
                'original_lines': [
                    self.current_lines[idx1],
                    self.current_lines[idx2]
                ],
                'suffixes': [suffix1, suffix2],
                'level': level,
                'needs_fix': needs_fix,
            })
        
        return issues
    
    def get_line_suggestions(self, line_idx: int, variation_type: str = 'all') -> list:
        """
        קבל הצעות לשינוי השורה השלמה.
        
        Args:
            line_idx: אינדקס השורה
            variation_type: סוג שינוי
                - 'last_word': רק החלפת מילה אחרונה
                - 'extend': הוספת מילים
                - 'rewrite': שכתוב השורה
                - 'all': כל השיטות
        
        Returns:
            list של הצעות
        """
        if line_idx >= len(self.current_lines):
            return []
        
        # מצא את השורה השותפה
        groups = self.get_rhyme_groups()
        partner_idx = None
        
        for group_name, line_indices in groups.items():
            if line_idx in line_indices:
                partner_idx = line_indices[0] if line_indices[1] == line_idx else line_indices[1]
                break
        
        if partner_idx is None:
            return []
        
        # קבל את הסיומת הרצויה (מהשורה השותפה)
        target_suffix = self.phonetic_suffixes[partner_idx]
        
        # קבל וריאציות
        result = suggest_line_variations(
            self.current_lines[line_idx],
            target_suffix,
            variation_type=variation_type
        )
        
        return result['variations']
    
    def apply_line_suggestion(self, line_idx: int, new_line: str) -> str:
        """החל הצעה לשורה."""
        if line_idx >= len(self.current_lines):
            return self.current_lines[line_idx]
        
        self.current_lines[line_idx] = new_line
        
        # עדכן מטא-דאטה
        self.metadata = vocalize_lines(self.current_lines)
        self.phonetic_suffixes = self._compute_suffixes()
        
        return self.current_lines[line_idx]
    
    def auto_improve(self, method: str = 'smart') -> dict:
        """
        שפר אוטומטית.
        
        Args:
            method: שיטת שיפור
                - 'last_word_only': רק החלפת מילה אחרונה
                - 'extend': הוספת מילים
                - 'rewrite': שכתוב שורות
                - 'smart': בחירה אוטומטית של השיטה הטובה ביותר
        
        Returns:
            dict עם תוצאות
        """
        issues = self.get_issues()
        changes = []
        
        for issue in issues:
            if not issue['needs_fix']:
                continue
            
            line_indices = issue['lines']
            
            # בחר שיטה
            if method == 'last_word_only':
                variation_type = 'last_word'
            elif method == 'extend':
                variation_type = 'extend'
            elif method == 'rewrite':
                variation_type = 'rewrite'
            else:  # smart
                variation_type = 'all'
            
            # קבל הצעות
            for line_idx in line_indices:
                suggestions = self.get_line_suggestions(line_idx, variation_type)
                
                if suggestions:
                    # בחר את ההצעה הטובה ביותר
                    best = suggestions[0]
                    original_line = self.current_lines[line_idx]
                    
                    # החל הצעה
                    self.apply_line_suggestion(line_idx, best['line'])
                    
                    changes.append({
                        'line_idx': line_idx,
                        'line_number': line_idx + 1,
                        'original': original_line,
                        'improved': best['line'],
                        'method': best['method'],
                        'level': best['level'],
                    })
                    break
        
        return {
            'original_lines': self.original_lines,
            'current_lines': self.current_lines,
            'changes': changes,
            'num_changes': len(changes),
        }
    
    def get_status(self) -> dict:
        """קבל סטטוס."""
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


def improve_poem_advanced(lines: list, pattern: str = None, method: str = 'smart') -> dict:
    """
    שפר שיר בצורה מתקדמת.
    
    Args:
        lines: רשימת שורות
        pattern: תבנית רצויה
        method: שיטת שיפור (last_word_only, extend, rewrite, smart)
    
    Returns:
        {
            'original_lines': [...],
            'improved_lines': [...],
            'changes': [...],
            'pattern': str,
            'num_issues_before': int,
            'num_issues_after': int,
        }
    """
    improver = AdvancedPoemImprover(lines, pattern)
    
    # קבל מצב לפני
    status_before = improver.get_status()
    
    # שפר
    result = improver.auto_improve(method=method)
    
    # קבל מצב אחרי
    status_after = improver.get_status()
    
    return {
        'original_lines': lines,
        'improved_lines': status_after['current_lines'],
        'pattern': status_after['pattern'],
        'changes': result['changes'],
        'num_changes': result['num_changes'],
        'num_issues_before': status_before['num_issues'],
        'num_issues_after': status_after['num_issues'],
        'is_complete': status_after['is_complete'],
    }
