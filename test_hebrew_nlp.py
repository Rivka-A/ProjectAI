"""
בדיקות למערכת BERT המשופרת.
"""
import unittest
from services.hebrew_completer import HebrewSentenceCompleter


class TestHebrewCompleter(unittest.TestCase):
    """בדיקות למודול HebrewSentenceCompleter."""
    
    def test_is_complete_word(self):
        """בדוק זיהוי מילים שלמות."""
        self.assertTrue(HebrewSentenceCompleter.is_complete_word("קטוע"))
        self.assertTrue(HebrewSentenceCompleter.is_complete_word("הלב"))
        self.assertFalse(HebrewSentenceCompleter.is_complete_word("ק"))
        self.assertFalse(HebrewSentenceCompleter.is_complete_word(""))
    
    def test_suggest_completion(self):
        """בדוק הצעות השלמה."""
        suggestions = HebrewSentenceCompleter.suggest_completion("קט")
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any(s.startswith("קט") for s in suggestions))
    
    def test_validate_sentence_structure(self):
        """בדוק תיקוף מבנה משפט."""
        self.assertTrue(HebrewSentenceCompleter.validate_sentence_structure("הלב שלי קטוע"))
        self.assertTrue(HebrewSentenceCompleter.validate_sentence_structure("בעולם הזה"))
        self.assertFalse(HebrewSentenceCompleter.validate_sentence_structure(""))
        self.assertFalse(HebrewSentenceCompleter.validate_sentence_structure("ק"))
    
    def test_fix_broken_line(self):
        """בדוק תיקון שורה קטועה."""
        broken = "הלב קטו"
        fixed = HebrewSentenceCompleter.fix_broken_line(broken)
        self.assertNotEqual(fixed, "")
        self.assertIn("הלב", fixed)
    
    def test_extract_rhyme_word(self):
        """בדוק חילוץ מילת חרוז."""
        line = "הלב שלי קטוע"
        rhyme_word = HebrewSentenceCompleter.extract_rhyme_word(line)
        self.assertEqual(rhyme_word, "קטוע")
    
    def test_ensure_grammatical_agreement(self):
        """בדוק הסכמה דקדוקית."""
        # זכר
        word = HebrewSentenceCompleter.ensure_grammatical_agreement("מלכים", "הוא")
        self.assertIn(word, ["מלכים", "מלכות"])
        
        # נקבה
        word = HebrewSentenceCompleter.ensure_grammatical_agreement("מלכות", "היא")
        self.assertIn(word, ["מלכים", "מלכות"])


class TestIntegration(unittest.TestCase):
    """בדיקות אינטגרציה."""
    
    def test_complete_broken_line_integration(self):
        """בדוק השלמת שורה קטועה."""
        from services.suggestion_service import complete_broken_line
        
        broken = "הלב קטו"
        completed = complete_broken_line(broken)
        self.assertIsNotNone(completed)
        self.assertGreater(len(completed), 0)
    
    def test_vocalize_lines_integration(self):
        """בדוק ניקוד שורות."""
        from services.suggestion_service import vocalize_lines
        
        lines = ["הלב שלי קטוע", "בעולם הזה"]
        metadata = vocalize_lines(lines)
        
        self.assertEqual(len(metadata), 2)
        self.assertIn('original_word', metadata[0])
        self.assertIn('last_word_vocalized', metadata[0])
        self.assertIn('stress_type', metadata[0])


if __name__ == '__main__':
    unittest.main()
