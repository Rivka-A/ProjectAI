"""
בקר UI - ניהול תיקון שורות עם פעולה מפורשת של המשתמש.
"""
from typing import Optional
from services.suggestion_service import complete_broken_line, get_enhanced_suggestions, vocalize_lines
from services.improved_rhyme_checker import ImprovedRhymeChecker
from core.rhyme_checker import RhymeChecker


class LineFixController:
    """
    בקר לניהול תיקון שורות בשיר.
    
    זרימה:
    1. המשתמש בוחר שורה בעייתית
    2. המערכת מציגה את הבעיה (לא מתקנת עדיין)
    3. המשתמש לוחץ "תקן" או בוחר הצעה
    4. רק אז המערכת מתקנת
    """
    
    def __init__(self):
        self.current_line_idx: Optional[int] = None
        self.current_line: Optional[str] = None
        self.current_metadata: Optional[dict] = None
        self.suggestions: list[str] = []
        self.is_fixed: bool = False
    
    def select_line(self, line: str, line_idx: int, all_lines: list[str]) -> dict:
        """
        בחר שורה לתיקון (לא מתקנת עדיין).
        מחזיר מידע על הבעיה.
        """
        self.current_line = line
        self.current_line_idx = line_idx
        self.is_fixed = False
        
        # קבל ניקוד
        metadata_list = vocalize_lines([line])
        self.current_metadata = metadata_list[0]
        
        # בדוק תקינות
        from services.bert_service import validate_line_completeness
        is_complete = validate_line_completeness(line)
        
        return {
            'line': line,
            'line_idx': line_idx,
            'is_complete': is_complete,
            'last_word': self.current_metadata['original_word'],
            'vocalized': self.current_metadata['last_word_vocalized'],
            'stress_type': self.current_metadata['stress_type'],
            'issue': self._get_issue_description(is_complete),
            'needs_fixing': not is_complete,
        }
    
    def _get_issue_description(self, is_complete: bool) -> str:
        """קבל תיאור של הבעיה."""
        if is_complete:
            return "השורה תקינה"
        else:
            return "השורה קטועה או לא תקינה תחבירית"
    
    def get_suggestions(self, all_lines: list[str], target_rhyme_key: Optional[tuple] = None,
                       min_rhyme_level: int = 2) -> list[tuple[str, int]]:
        """
        קבל הצעות לתיקון (לא מתקנת עדיין).
        מחזיר רשימה של (הצעה, רמת_חרוז).
        """
        if not self.current_line or not self.current_metadata:
            return []
        
        # קבל הצעות בסיסיות
        from services.suggestion_service import get_enhanced_suggestions
        
        if target_rhyme_key is None:
            target_rhyme_key = RhymeChecker.extract_rhyme_key(
                self.current_metadata['last_word_vocalized'],
                self.current_metadata['stress_type']
            )
        
        raw_suggestions = get_enhanced_suggestions(
            lines=all_lines,
            line_idx=self.current_line_idx,
            bad_word=self.current_metadata['original_word'],
            target_key=target_rhyme_key,
            orig_level=5,  # קבל הכל בהתחלה
            rejected_words=set()
        )
        
        # דרג לפי חריזה
        ranked = ImprovedRhymeChecker.rank_suggestions_by_rhyme_quality(
            raw_suggestions,
            self.current_metadata['last_word_vocalized'],
            self.current_metadata['stress_type']
        )
        
        self.suggestions = [s for s, _ in ranked]
        return ranked
    
    def fix_line_with_suggestion(self, suggestion: str) -> dict:
        """
        תקן את השורה עם הצעה מסוימת.
        זה מתבצע רק כשהמשתמש בוחר הצעה.
        """
        if not self.current_line:
            return {'error': 'אין שורה נבחרת'}
        
        # החלף את המילה האחרונה
        words = self.current_line.split()
        if words:
            words[-1] = suggestion
            fixed_line = ' '.join(words)
        else:
            fixed_line = suggestion
        
        self.current_line = fixed_line
        self.is_fixed = True
        
        # קבל ניקוד חדש
        metadata_list = vocalize_lines([fixed_line])
        self.current_metadata = metadata_list[0]
        
        return {
            'original': self.current_line,
            'fixed': fixed_line,
            'suggestion': suggestion,
            'is_fixed': True,
            'new_metadata': self.current_metadata,
        }
    
    def fix_line_automatically(self) -> dict:
        """
        תקן את השורה אוטומטית (בלי הצעה).
        זה מתבצע רק כשהמשתמש לוחץ "תקן אוטומטית".
        """
        if not self.current_line:
            return {'error': 'אין שורה נבחרת'}
        
        # תקן באמצעות המערכת
        fixed_line = complete_broken_line(self.current_line)
        
        self.current_line = fixed_line
        self.is_fixed = True
        
        # קבל ניקוד חדש
        metadata_list = vocalize_lines([fixed_line])
        self.current_metadata = metadata_list[0]
        
        return {
            'original': self.current_line,
            'fixed': fixed_line,
            'is_fixed': True,
            'new_metadata': self.current_metadata,
        }
    
    def cancel_fix(self) -> dict:
        """בטל את התיקון."""
        self.is_fixed = False
        self.suggestions = []
        
        return {
            'cancelled': True,
            'current_line': self.current_line,
        }
    
    def get_current_state(self) -> dict:
        """קבל את המצב הנוכחי."""
        return {
            'line': self.current_line,
            'line_idx': self.current_line_idx,
            'metadata': self.current_metadata,
            'is_fixed': self.is_fixed,
            'suggestions': self.suggestions,
        }


class PoemRhymeController:
    """
    בקר לניהול חריזה של שיר שלם.
    
    זרימה:
    1. טען שיר
    2. בדוק חריזה (לא מתקן עדיין)
    3. המשתמש בוחר שורות לתיקון
    4. תקן רק את השורות שנבחרו
    """
    
    def __init__(self):
        self.lines: list[str] = []
        self.metadata: list[dict] = []
        self.rhyme_issues: list[dict] = []
        self.fixed_lines: set[int] = set()
    
    def load_poem(self, lines: list[str]) -> dict:
        """
        טען שיר (לא מתקן עדיין).
        """
        self.lines = lines
        self.metadata = vocalize_lines(lines)
        self.fixed_lines = set()
        
        # בדוק חריזה
        self._analyze_rhyme_scheme()
        
        return {
            'lines': lines,
            'metadata': self.metadata,
            'rhyme_issues': self.rhyme_issues,
            'num_issues': len(self.rhyme_issues),
        }
    
    def _analyze_rhyme_scheme(self):
        """בדוק תבנית חריזה."""
        self.rhyme_issues = []
        
        if len(self.lines) < 2:
            return
        
        # קבל מפתחות חרוז
        rhyme_keys = []
        for meta in self.metadata:
            key = RhymeChecker.extract_rhyme_key(
                meta['last_word_vocalized'],
                meta['stress_type']
            )
            rhyme_keys.append(key)
        
        # בדוק זוגות צפויים
        expected_pairs = self._get_expected_pairs()
        
        for idx1, idx2 in expected_pairs:
            if idx1 >= len(rhyme_keys) or idx2 >= len(rhyme_keys):
                continue
            
            level = RhymeChecker.rhyme_level(rhyme_keys[idx1], rhyme_keys[idx2])
            
            # בדוק אם זה חריג
            is_exception = ImprovedRhymeChecker._is_phonetic_exception(
                rhyme_keys[idx1], rhyme_keys[idx2]
            )
            
            if level > 2 or is_exception:
                self.rhyme_issues.append({
                    'lines': (idx1 + 1, idx2 + 1),
                    'words': (
                        self.metadata[idx1]['original_word'],
                        self.metadata[idx2]['original_word']
                    ),
                    'level': level,
                    'is_exception': is_exception,
                    'issue_type': self._get_issue_type(level, is_exception),
                })
    
    def _get_expected_pairs(self) -> list[tuple[int, int]]:
        """קבל זוגות צפויים לחריזה."""
        num_lines = len(self.lines)
        
        if num_lines == 4:
            # בדוק תבנית
            rhyme_keys = [
                RhymeChecker.extract_rhyme_key(m['last_word_vocalized'], m['stress_type'])
                for m in self.metadata
            ]
            
            score_aabb = (rhyme_keys[0] == rhyme_keys[1]) + (rhyme_keys[2] == rhyme_keys[3])
            score_abab = (rhyme_keys[0] == rhyme_keys[2]) + (rhyme_keys[1] == rhyme_keys[3])
            score_abba = (rhyme_keys[0] == rhyme_keys[3]) + (rhyme_keys[1] == rhyme_keys[2])
            
            if score_aabb >= score_abab and score_aabb >= score_abba:
                return [(0, 1), (2, 3)]
            elif score_abba >= score_abab:
                return [(0, 3), (1, 2)]
            else:
                return [(0, 2), (1, 3)]
        else:
            return [(i, i + 1) for i in range(num_lines - 1)]
    
    def _get_issue_type(self, level: int, is_exception: bool) -> str:
        """קבל סוג הבעיה."""
        if is_exception:
            return "חריג פונטי"
        
        types = {
            2: "חרוז טוב",
            3: "עיצור משותף",
            4: "תנועה משותפת",
            5: "אין חרוז",
        }
        
        return types.get(level, "לא ידוע")
    
    def fix_line(self, line_idx: int, suggestion: Optional[str] = None) -> dict:
        """
        תקן שורה מסוימת.
        זה מתבצע רק כשהמשתמש בוחר לתקן.
        """
        if line_idx >= len(self.lines):
            return {'error': 'אינדקס שורה לא תקין'}
        
        if suggestion:
            # תקן עם הצעה
            words = self.lines[line_idx].split()
            if words:
                words[-1] = suggestion
                self.lines[line_idx] = ' '.join(words)
        else:
            # תקן אוטומטית
            self.lines[line_idx] = complete_broken_line(self.lines[line_idx])
        
        self.fixed_lines.add(line_idx)
        
        # עדכן מטא-דאטה
        self.metadata = vocalize_lines(self.lines)
        
        # בדוק חריזה שוב
        self._analyze_rhyme_scheme()
        
        return {
            'line_idx': line_idx,
            'fixed_line': self.lines[line_idx],
            'remaining_issues': len(self.rhyme_issues),
        }
    
    def get_poem_status(self) -> dict:
        """קבל סטטוס של השיר."""
        return {
            'lines': self.lines,
            'metadata': self.metadata,
            'rhyme_issues': self.rhyme_issues,
            'fixed_lines': list(self.fixed_lines),
            'num_issues': len(self.rhyme_issues),
            'is_complete': len(self.rhyme_issues) == 0,
        }
    
    def get_suggestions_for_line(self, line_idx: int, min_rhyme_level: int = 2) -> list[tuple[str, int]]:
        """קבל הצעות לשורה מסוימת."""
        if line_idx >= len(self.lines):
            return []
        
        target_key = RhymeChecker.extract_rhyme_key(
            self.metadata[line_idx]['last_word_vocalized'],
            self.metadata[line_idx]['stress_type']
        )
        
        from services.suggestion_service import get_enhanced_suggestions
        
        raw_suggestions = get_enhanced_suggestions(
            lines=self.lines,
            line_idx=line_idx,
            bad_word=self.metadata[line_idx]['original_word'],
            target_key=target_key,
            orig_level=5,
            rejected_words=set()
        )
        
        # דרג לפי חריזה
        ranked = ImprovedRhymeChecker.rank_suggestions_by_rhyme_quality(
            raw_suggestions,
            self.metadata[line_idx]['last_word_vocalized'],
            self.metadata[line_idx]['stress_type']
        )
        
        return ranked
