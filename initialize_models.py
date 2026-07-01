"""
סקריפט אתחול - הורדת ואתחול מודלים.
הרץ פעם אחת בתחילת השימוש.
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_models():
    """הורד ואתחל את כל המודלים הדרושים."""
    logger.info("מתחיל אתחול מערכת BERT המשופרת...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForMaskedLM, AutoModelForSeq2SeqLM
        import torch
        
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        
        # הורד HeBERT
        logger.info("הורדת HeBERT...")
        try:
            tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
            model = AutoModelForMaskedLM.from_pretrained("avichr/heBERT")
            logger.info("✓ HeBERT הורד בהצלחה")
        except Exception as e:
            logger.warning(f"⚠ לא הצליח להוריד HeBERT: {e}")
            logger.info("  המערכת תשתמש במודל המקומי כ-fallback")
        
        # הורד mT5
        logger.info("הורדת mT5...")
        try:
            tokenizer = AutoTokenizer.from_pretrained("google/mt5-small")
            model = AutoModelForSeq2SeqLM.from_pretrained("google/mt5-small")
            logger.info("✓ mT5 הורד בהצלחה")
        except Exception as e:
            logger.warning(f"⚠ לא הצליח להוריד mT5: {e}")
            logger.info("  השלמת משפטים לא תהיה זמינה")
        
        logger.info("✓ אתחול הושלם בהצלחה!")
        return True
        
    except ImportError as e:
        logger.error(f"✗ שגיאה: {e}")
        logger.error("הרץ: pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"✗ שגיאה בלתי צפויה: {e}")
        return False


def test_models():
    """בדוק שהמודלים עובדים."""
    logger.info("\nבדיקת מודלים...")
    
    try:
        from services.bert_service import get_fill_mask_suggestions, validate_line_completeness
        from services.hebrew_completer import HebrewSentenceCompleter
        
        # בדוק HebrewSentenceCompleter
        logger.info("בדיקת HebrewSentenceCompleter...")
        result = HebrewSentenceCompleter.is_complete_word("קטוע")
        logger.info(f"  is_complete_word('קטוע'): {result}")
        
        # בדוק validate_line_completeness
        logger.info("בדיקת validate_line_completeness...")
        result = validate_line_completeness("הלב שלי קטוע")
        logger.info(f"  validate_line_completeness('הלב שלי קטוע'): {result}")
        
        logger.info("✓ כל הבדיקות עברו בהצלחה!")
        return True
        
    except Exception as e:
        logger.error(f"✗ שגיאה בבדיקה: {e}")
        return False


def main():
    """פונקציה ראשית."""
    logger.info("=" * 50)
    logger.info("אתחול מערכת BERT המשופרת")
    logger.info("=" * 50)
    
    # אתחל מודלים
    if not initialize_models():
        logger.error("אתחול נכשל!")
        sys.exit(1)
    
    # בדוק מודלים
    if not test_models():
        logger.warning("חלק מהבדיקות נכשלו, אבל המערכת עשויה עדיין לעבוד")
    
    logger.info("=" * 50)
    logger.info("אתחול הושלם!")
    logger.info("=" * 50)
    logger.info("\nהשתמש בפונקציות הבאות:")
    logger.info("  - complete_broken_line() - השלמת שורה קטועה")
    logger.info("  - get_enhanced_suggestions() - הצעות משופרות")
    logger.info("  - validate_line_completeness() - בדיקת תקינות")
    logger.info("\nראה HEBREW_NLP_README.md לפרטים נוספים")


if __name__ == "__main__":
    main()
