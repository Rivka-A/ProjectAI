
"""
שירות BERT - חיזוי מילים חסרות באמצעות מודל השפה HeBERT.
"""
import os
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM, AutoModelForSeq2SeqLM, pipeline as hf_pipeline

from transformers import pipeline
os.environ["HF_TOKEN"] = "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"

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(_BASE, "moduls")
#סינון שמות הקודש
_FORBIDDEN_CHARS_COLLECTION = {
    ('י', 'ה', 'ו', 'ה'),
    ('א', 'ד', 'נ', 'י'),
    ('א', 'ל', 'ה', 'י', 'ם'),
    ('א', 'ל', 'ו', 'ה', 'י', 'ם'),
    ('ש', 'ד', 'י'),
    ('צ', 'ב', 'א', 'ו', 'ת'),
    ('א', 'ל'),
}
FORBIDDEN_WORDS = {"".join(t) for t in _FORBIDDEN_CHARS_COLLECTION}

# משתנים גלובליים ומניעת טוקנים ריקים
SKIP_TOKENS = {"[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"}
# HeBERT - מודל BERT חזק בעברית
try:
    _tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
    _model = AutoModelForMaskedLM.from_pretrained("avichr/heBERT")
    _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer, device=0 if torch.cuda.is_available() else -1)
except Exception:
    print("HeBERT not available, falling back to local model.")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    _model = AutoModelForMaskedLM.from_pretrained(MODEL_DIR)
    _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer)


def is_valid_word(word: str) -> bool:
    """בדיקה בסיסית שהמילה המוחזרת מכילה תווים בעברית ותקנית."""
    if not word:
        return False
    # סינון טוקנים של תתי-מילים או תווים מיוחדים
    if word.startswith("##") or word.startswith("["):
        return False
    # סינון מילים אסורות
    if word in FORBIDDEN_WORDS:
        return False
    return any('\u05D0' <= c <= '\u05EA' for c in word)


def get_fill_mask_suggestions(masked_context: str, top_k: int = 50) -> list[str]:
    """
    מבצע חיזוי עבור הקשר בודד המכיל [MASK].
    מקבל מחרוזת אחת ומחזיר רשימה שטוחה של מילים מוצעות.
    """
    if not _fill_mask or not masked_context or "[MASK]" not in masked_context:
        return []
    try:
        results = _fill_mask(masked_context, top_k=top_k)
        # נרמול התוצאה במידה והמודל החזיר דיקשנרי בודד במקום רשימה
        if isinstance(results, dict):
            results = [results]
            
        return [
            r["token_str"].strip() 
            for r in results 
            if r.get("token_str") 
            and r["token_str"].strip() not in SKIP_TOKENS 
            and is_valid_word(r["token_str"])
        ]
    except Exception as e:
        print(f"Error in get_fill_mask_suggestions: {e}")
        return []


def get_batch_fill_mask_suggestions(contexts: list[str], top_k: int = 50) -> list[list[str]]:
    """
    מבצע חיזוי מרוכז (Batch) עבור רשימה של הקשרים (כל אחד עם [MASK]).
    מחזיר רשימה דו-ממדית שבה כל איבר הוא רשימת מילים מוצעות להקשר המתאים.
    """
    if not _fill_mask or not contexts:
        return []
    try:
        batch_results = _fill_mask(contexts, top_k=top_k, batch_size=len(contexts))
        
        # נרמול למבנה דו-ממדי קבוע (Hugging Face מחזיר מבנה שטוח עבור איבר בודד)
        if len(contexts) == 1 and batch_results and not isinstance(batch_results[0], list):
            batch_results = [batch_results]
            
        final_results = []
        for results in batch_results:
            suggestions = [
                r["token_str"].strip() 
                for r in results 
                if r.get("token_str") 
                and r["token_str"].strip() not in SKIP_TOKENS 
                and is_valid_word(r["token_str"])
            ]
            final_results.append(suggestions)
        return final_results
    except Exception as e:
        print(f"Error in batch suggestions: {e}")
        return []


def get_contextual_suggestions(context: str, position: int, top_k: int = 30) -> list[str]:
    """
    מחזיר הצעות מילים בהתחשב בהקשר מלא של השורה במיקום המבוקש.
    """
    try:
        words = context.split()
        if position >= len(words):
            words.append('[MASK]')
        else:
            words[position] = '[MASK]'
        masked_context = " ".join(words)
        
        return get_fill_mask_suggestions(masked_context, top_k=top_k)
    except Exception as e:
        print(f"Error in get_contextual_suggestions: {e}")
        return []