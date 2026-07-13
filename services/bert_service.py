# """
# שירות BERT חזק בעברית: HeBERT + Seq2Seq להשלמת משפטים תקינים.
# """
# import os
# import torch
# import json
# import threading

# from datetime import datetime
# import ssl
# import urllib3
# ssl._create_default_https_context = ssl._create_unverified_context
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# os.environ["HF_TOKEN"] = "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"

# from transformers import AutoTokenizer, AutoModelForMaskedLM, AutoModelForSeq2SeqLM, pipeline as hf_pipeline
# from services.hebrew_completer import HebrewSentenceCompleter

# _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MODEL_DIR = os.path.join(_BASE, "moduls")
# _LOG_PATH = os.path.join(_BASE, "bert_suggestions_log.jsonl")

# _FORBIDDEN_CHARS_COLLECTION = {
#     ('י', 'ה', 'ו', 'ה'),
#     ('א', 'ד', 'נ', 'י'),
#     ('א', 'ל', 'ה', 'י', 'ם'),
#     ('א', 'ל', 'ו', 'ה', 'י', 'ם'),
#     ('ש', 'ד', 'י'),
#     ('צ', 'ב', 'א', 'ו', 'ת'),
#     ('א', 'ל'),
# }
# FORBIDDEN_WORDS = {"".join(t) for t in _FORBIDDEN_CHARS_COLLECTION}

# SKIP_TOKENS = {'.', ',', '!', '?', '[MASK]', ':', '-', '"', "'", '[CLS]', '[SEP]', '[PAD]'}

# _fill_mask = None
# _text_generation = None
# _fill_mask_lock = threading.Lock()
# _text_generation_lock = threading.Lock()


# def is_valid_word(word: str) -> bool:
#     if not word:
#         return False
#     w = word.strip()
#     if w.startswith("##") or w.startswith("Ġ"):
#         return False
#     return w not in FORBIDDEN_WORDS


# def _log_suggestions(original_line: str, masked_context: str, suggestions: list) -> None:
#     entry = {
#         "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "original_line": original_line,
#         "masked_context": masked_context,
#         "suggestions": suggestions,
#     }
#     with open(_LOG_PATH, "a", encoding="utf-8") as f:
#         f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# def _load_fill_mask():
#     global _fill_mask
#     if _fill_mask is not None:
#         return _fill_mask
#     with _fill_mask_lock:
#         if _fill_mask is not None:
#             return _fill_mask
#         device = 0 if torch.cuda.is_available() else -1
#         tok = AutoTokenizer.from_pretrained(MODEL_DIR)
#         mdl = AutoModelForMaskedLM.from_pretrained(MODEL_DIR)
#         _fill_mask = hf_pipeline("fill-mask", model=mdl, tokenizer=tok, device=device)
#     return _fill_mask


# def _load_text_generation():
#     global _text_generation
#     if _text_generation is not None:
#         return _text_generation
#     with _text_generation_lock:
#         if _text_generation is not None:
#             return _text_generation
#         try:
#             device = 0 if torch.cuda.is_available() else -1
#             tok = AutoTokenizer.from_pretrained("google/mt5-small")
#             mdl = AutoModelForSeq2SeqLM.from_pretrained("google/mt5-small")
#             _text_generation = hf_pipeline("text2text-generation", model=mdl, tokenizer=tok, device=device)
#         except Exception:
#             _text_generation = None
#     return _text_generation


# def get_fill_mask_suggestions(stanza_lines: list, target_idx: int, original_word: str, top_k: int = 50) -> list:
#     """מחזיר רשימת מילים מוצעות להחלפת original_word בשורה target_idx."""
#     masked = list(stanza_lines)
#     line = masked[target_idx]
#     original_line = line
#     if original_word in line:
#         prefix = line.rsplit(original_word, 1)[0].rstrip()
#     else:
#         prefix = line.rstrip()
#     if not prefix and not line.strip():
#         return []
#     masked[target_idx] = f"{prefix} [MASK]".strip()
#     context = " ".join(masked)
#     try:
#         results = _load_fill_mask()(context, top_k=top_k)
#         suggestions = [
#             r["token_str"].strip()
#             for r in results
#             if r.get("token_str")
#             and r["token_str"].strip() not in SKIP_TOKENS
#             and is_valid_word(r["token_str"])
#         ]
#         _log_suggestions(original_line, context, suggestions)
#         return suggestions
#     except Exception:
#         return []


# def complete_sentence(partial_line: str, max_length: int = 20) -> str:
#     if not partial_line.strip():
#         return partial_line
#     fixed = HebrewSentenceCompleter.fix_broken_line(partial_line)
#     if _load_text_generation() and fixed == partial_line:
#         try:
#             prompt = f"complete Hebrew: {partial_line}"
#             result = _load_text_generation()(prompt, max_length=max_length, num_beams=3)
#             if result and result[0].get('generated_text'):
#                 return result[0]['generated_text'].replace(prompt, "").strip()
#         except Exception:
#             pass
#     return fixed


# def get_contextual_suggestions(context: str, position: int, top_k: int = 30) -> list:
#     try:
#         words = context.split()
#         if position >= len(words):
#             words.append('[MASK]')
#         else:
#             words[position] = '[MASK]'
#         masked_context = " ".join(words)
#         results = _load_fill_mask()(masked_context, top_k=top_k)
#         return [
#             r["token_str"].strip()
#             for r in results
#             if r.get("token_str")
#             and r["token_str"].strip() not in SKIP_TOKENS
#             and is_valid_word(r["token_str"])
#         ]
#     except Exception:
#         return []


# def validate_line_completeness(line: str) -> bool:
#     return HebrewSentenceCompleter.validate_sentence_structure(line)


# """
# שירות BERT חזק בעברית: HeBERT + Seq2Seq להשלמת משפטים תקינים.
# """
# import os
# import torch
# from transformers import AutoTokenizer, AutoModelForMaskedLM, AutoModelForSeq2SeqLM, pipeline as hf_pipeline
# from services.hebrew_completer import HebrewSentenceCompleter

# os.environ["HF_TOKEN"] = "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"

# _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MODEL_DIR = os.path.join(_BASE, "moduls")
# try:
#     _tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
#     _model = AutoModelForMaskedLM.from_pretrained("avichr/heBERT")
#     _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer, device=0 if torch.cuda.is_available() else -1)

# # HeBERT - מודל BERT חזק בעברית
# # try:
# #     _tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
# #     _model = AutoModelForMaskedLM.from_pretrained("avichr/heBERT")
# #     _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer, device=0 if torch.cuda.is_available() else -1)
# except Exception:
#     # fallback למודל מקומי אם HeBERT לא זמין
#     _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
#     _model = AutoModelForMaskedLM.from_pretrained(MODEL_DIR)
#     _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer)

# # Seq2Seq להשלמת משפטים תקינים
# try:
#     _seq2seq_tokenizer = AutoTokenizer.from_pretrained("google/mt5-small")
#     _seq2seq_model = AutoModelForSeq2SeqLM.from_pretrained("google/mt5-small")
#     _text_generation = hf_pipeline("text2text-generation", model=_seq2seq_model, tokenizer=_seq2seq_tokenizer, device=0 if torch.cuda.is_available() else -1)
# except Exception:
#     _seq2seq_tokenizer = None
#     _seq2seq_model = None
#     _text_generation = None

# SKIP_TOKENS = {'.', ',', '!', '?', '[MASK]', ':', '-', '"', "'", '[CLS]', '[SEP]', '[PAD]'}


# def get_fill_mask_suggestions(stanza_lines: list[str], target_idx: int, original_word: str, top_k: int = 30) -> list[str]:
#     """מחזיר רשימת מילים מוצעות להחלפת original_word בשורה target_idx."""
#     masked = list(stanza_lines)
#     line = masked[target_idx]
#     prefix = line.rsplit(original_word, 1)[0].strip() if original_word in line else line.strip()
#     masked[target_idx] = f"{prefix} [MASK]"
#     context = " ".join(masked)
#     try:
#         results = _fill_mask(context, top_k=top_k)
#         return [r["token_str"].strip() for r in results if r.get("token_str") and r["token_str"].strip() not in SKIP_TOKENS]
#     except Exception:
#         return []


# def complete_sentence(partial_line: str, max_length: int = 20) -> str:
#     """
#     משלים משפט קטוע לביטוי תקין תחבירית.
#     משתמש ב-Seq2Seq + Hebrew grammar rules להשלמה חזקה.
#     """
#     if not partial_line.strip():
#         return partial_line
    
#     # תחילה נסה להשתמש בכללי דקדוק עברי
#     fixed = HebrewSentenceCompleter.fix_broken_line(partial_line)
    
#     # אם זה לא עזר, נסה Seq2Seq
#     if _text_generation and fixed == partial_line:
#         try:
#             prompt = f"complete Hebrew: {partial_line}"
#             result = _text_generation(prompt, max_length=max_length, num_beams=3)
#             if result and result[0].get('generated_text'):
#                 return result[0]['generated_text'].replace(prompt, "").strip()
#         except Exception:
#             pass
    
#     return fixed


# def get_contextual_suggestions(context: str, position: int, top_k: int = 30) -> list[str]:
#     """
#     מחזיר הצעות מילים בהתחשב בהקשר מלא של השורה.
#     משתמש ב-HeBERT עם הקשר רחב יותר.
#     """
#     try:
#         # הוסף [MASK] בעמדה המבוקשת
#         words = context.split()
#         if position >= len(words):
#             words.append('[MASK]')
#         else:
#             words[position] = '[MASK]'
#         masked_context = " ".join(words)
        
#         results = _fill_mask(masked_context, top_k=top_k)
#         suggestions = [r["token_str"].strip() for r in results if r.get("token_str") and r["token_str"].strip() not in SKIP_TOKENS]
#         return suggestions
#     except Exception:
#         return []


# def validate_line_completeness(line: str) -> bool:
#     """בדוק אם השורה שלמה ותקינה תחבירית."""
#     return HebrewSentenceCompleter.validate_sentence_structure(line)


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

# HeBERT - מודל BERT חזק בעברית
try:
    _tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
    _model = AutoModelForMaskedLM.from_pretrained("avichr/heBERT")
    _fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer, device=0 if torch.cuda.is_available() else -1)
except Exception:
    print("HeBERT not available, falling back to local model.")
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
    print("Seq2Seq model not available. bert_service line 308")
    _seq2seq_tokenizer = None
    _seq2seq_model = None
    _text_generation = None

SKIP_TOKENS = {'.', ',', '!', '?', '[MASK]', ':', '-', '"', "'", '[CLS]', '[SEP]', '[PAD]'}
def is_valid_word(word: str) -> bool:
    if not word:
        return False
    w = word.strip()
    if w.startswith("##") or w.startswith("Ġ"):
        return False
    return w not in FORBIDDEN_WORDS


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
    except Exception as e:
        print(f"Error in get_fill_mask_suggestions bert_service line 334: {e}")
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
        except Exception as e:
            print(f"Error in complete_sentence bert_service line 350: {e}")
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
        suggestions = [r["token_str"].strip() for r in results if r.get("token_str") and r["token_str"].strip() not in SKIP_TOKENS and is_valid_word(r["token_str"])]

        return suggestions
    except Exception as e:
        print(f"Error in get_contextual_suggestions bert_service line 382: {e}")
        return []


def validate_line_completeness(line: str) -> bool:
    """בדוק אם השורה שלמה ותקינה תחבירית."""
    return HebrewSentenceCompleter.validate_sentence_structure(line)