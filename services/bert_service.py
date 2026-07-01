"""
שירות BERT חזק בעברית: HeBERT + Seq2Seq להשלמת משפטים תקינים.
"""
import os
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM, AutoModelForSeq2SeqLM, pipeline as hf_pipeline
from services.hebrew_completer import HebrewSentenceCompleter

os.environ["HF_TOKEN"] = "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"

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(_BASE, "moduls")
try:
    _tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
    _model = AutoModelForMaskedLM.from_pretrained("avichr/heBERT")
    _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer, device=0 if torch.cuda.is_available() else -1)

# HeBERT - מודל BERT חזק בעברית
# try:
#     _tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
#     _model = AutoModelForMaskedLM.from_pretrained("avichr/heBERT")
#     _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer, device=0 if torch.cuda.is_available() else -1)
except Exception:
    # fallback למודל מקומי אם HeBERT לא זמין
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    _model = AutoModelForMaskedLM.from_pretrained(MODEL_DIR)
    _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer)

# Seq2Seq להשלמת משפטים תקינים
try:
    _seq2seq_tokenizer = AutoTokenizer.from_pretrained("google/mt5-small")
    _seq2seq_model = AutoModelForSeq2SeqLM.from_pretrained("google/mt5-small")
    _text_generation = hf_pipeline("text2text-generation", model=_seq2seq_model, tokenizer=_seq2seq_tokenizer, device=0 if torch.cuda.is_available() else -1)
except Exception:
    _seq2seq_tokenizer = None
    _seq2seq_model = None
    _text_generation = None

SKIP_TOKENS = {'.', ',', '!', '?', '[MASK]', ':', '-', '"', "'", '[CLS]', '[SEP]', '[PAD]'}


def get_fill_mask_suggestions(stanza_lines: list[str], target_idx: int, original_word: str, top_k: int = 30) -> list[str]:
    """מחזיר רשימת מילים מוצעות להחלפת original_word בשורה target_idx."""
    masked = list(stanza_lines)
    line = masked[target_idx]
    prefix = line.rsplit(original_word, 1)[0].strip() if original_word in line else line.strip()
    masked[target_idx] = f"{prefix} [MASK]"
    context = " ".join(masked)
    try:
        results = _fill_mask(context, top_k=top_k)
        return [r["token_str"].strip() for r in results if r.get("token_str") and r["token_str"].strip() not in SKIP_TOKENS]
    except Exception:
        return []


def complete_sentence(partial_line: str, max_length: int = 20) -> str:
    """
    משלים משפט קטוע לביטוי תקין תחבירית.
    משתמש ב-Seq2Seq + Hebrew grammar rules להשלמה חזקה.
    """
    if not partial_line.strip():
        return partial_line
    
    # תחילה נסה להשתמש בכללי דקדוק עברי
    fixed = HebrewSentenceCompleter.fix_broken_line(partial_line)
    
    # אם זה לא עזר, נסה Seq2Seq
    if _text_generation and fixed == partial_line:
        try:
            prompt = f"complete Hebrew: {partial_line}"
            result = _text_generation(prompt, max_length=max_length, num_beams=3)
            if result and result[0].get('generated_text'):
                return result[0]['generated_text'].replace(prompt, "").strip()
        except Exception:
            pass
    
    return fixed


def get_contextual_suggestions(context: str, position: int, top_k: int = 30) -> list[str]:
    """
    מחזיר הצעות מילים בהתחשב בהקשר מלא של השורה.
    משתמש ב-HeBERT עם הקשר רחב יותר.
    """
    try:
        # הוסף [MASK] בעמדה המבוקשת
        words = context.split()
        if position >= len(words):
            words.append('[MASK]')
        else:
            words[position] = '[MASK]'
        masked_context = " ".join(words)
        
        results = _fill_mask(masked_context, top_k=top_k)
        suggestions = [r["token_str"].strip() for r in results if r.get("token_str") and r["token_str"].strip() not in SKIP_TOKENS]
        return suggestions
    except Exception:
        return []


def validate_line_completeness(line: str) -> bool:
    """בדוק אם השורה שלמה ותקינה תחבירית."""
    return HebrewSentenceCompleter.validate_sentence_structure(line)
