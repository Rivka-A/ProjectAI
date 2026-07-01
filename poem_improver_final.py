"""
משפר חריזה - עם בדיקת סיומת פונטית נכונה.
"""
from services.phonetic_rhyme_checker import (
    get_phonetic_suffix,
    compare_phonetic_suffixes,
    is_rhyme,
    get_rhyme_quality,
    rank_words_by_rhyme,
)
from services.improved_suggestion_service import (
    vocalize_lines,
    get_suggestions_by_rhyme,
)
from services.rhyme_analyzer import detect_rhyme_pattern


class PoemImprover:
    """
    משפר חריזה עם בדיקת סיומת פונטית נכונה.
    """
    
    def __init__(self, lines: list, pattern: str = None):
        """אתחל עם שיר ותבנית רצויה."""
        self.original_lines = lines
        self.current_lines = lines.copy()
        self.metadata = vocalize_lines(lines)
        
        # זהה תבנית אוטומטית
        if pattern:
            self.target_pattern = pattern
        else:
            detected = detect_rhyme_pattern(lines)
            self.target_pattern = detected['pattern']
        
        # חשב סיומות פונטיות
        self.phonetic_suffixes = self._compute_phonetic_suffixes()
    
    def _compute_phonetic_suffixes(self) -> list:
        """חשב סיומות פונטיות לכל שורה."""
        suffixes = []
        for meta in self.metadata:
            suffix = get_phonetic_suffix(
                meta['last_word_vocalized'],
                meta['stress_type']
            )
            suffixes.append(suffix)
        return suffixes
    
    def get_rhyme_groups(self) -> dict:
        """קבל קבוצות חריזה לפי התבנית."""
        if self.target_pattern == 'ABBA':
            return {'A': [0, 3], 'B': [1, 2]}
        elif self.target_pattern == 'AABB':
            return {'A': [0, 1], 'B': [2, 3]}
        elif self.target_pattern == 'ABAB':
            return {'A': [0, 2], 'B': [1, 3]}
        else:
            return {'A': [0, 1], 'B': [2, 3]}
    
    def get_issues(self) -> list:
        """קבל בעיות חריזה לפי סיומת פונטית."""
        issues = []
        groups = self.get_rhyme_groups()
        
        for group_name, line_indices in groups.items():
            if len(line_indices) != 2:
                continue
            
            idx1, idx2 = line_indices
            
            # קבל סיומות פונטיות
            suffix1 = self.phonetic_suffixes[idx1]
            suffix2 = self.phonetic_suffixes[idx2]
            
            # בדוק איכות חרוז
            quality = get_rhyme_quality(
                self.metadata[idx1]['last_word_vocalized'],
                self.metadata[idx2]['last_word_vocalized']
            )
            
            level = quality['level']
            needs_fix = level > 2  # רק חרוז מושלם או טוב
            
            issues.append({
                'group': group_name,
                'lines': line_indices,
                'line_numbers': [idx1 + 1, idx2 + 1],
                'words': [
                    self.metadata[idx1]['original_word'],
                    self.metadata[idx2]['original_word']
                ],
                'suffix1': suffix1,
                'suffix2': suffix2,
                'level': level,
                'needs_fix': needs_fix,
                'explanation': quality['explanation'],
            })
        
        return issues
    
    def get_suggestions_for_line(self, line_idx: int) -> list:
        """קבל הצעות לשורה לפי סיומת פונטית נכונה."""
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
        
        # קבל הצעות בסיסיות
        raw_suggestions = get_suggestions_by_rhyme(
            self.current_lines,
            line_idx,
            self.metadata[line_idx]['original_word'],
            self.phonetic_suffixes[partner_idx],  # סיומת פונטית
            5,
            set()
        )
        
        if not raw_suggestions:
            return []
        
        # דרג לפי סיומת פונטית
        ranked = rank_words_by_rhyme(
            [w for w, _ in raw_suggestions],
            self.metadata[partner_idx]['last_word_vocalized']
        )
        
        return ranked[:10]
    
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
            self.phonetic_suffixes = self._compute_phonetic_suffixes()
        
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
        issues = self.get_issues()
        
        for issue in issues:
            if not issue['needs_fix']:
                continue
            
            line_indices = issue['lines']
            
            for line_idx in line_indices:
                suggestions = self.get_suggestions_for_line(line_idx)
                if suggestions:
                    best_word = suggestions[0][0]
                    self.apply_suggestion(line_idx, best_word)
                    break
        
        return self.get_status()


def improve_poem_correct(lines: list, pattern: str = None) -> dict:
    """
    שפר שיר עם בדיקת סיומת פונטית נכונה.
    
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
