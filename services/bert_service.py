"""
שירות BERT מקומי: טעינת המודל וקריאות fill-mask.
"""
import os
from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline as hf_pipeline

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(_BASE, "moduls")

_tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
_model = AutoModelForMaskedLM.from_pretrained(MODEL_DIR)
_fill_mask = hf_pipeline("fill-mask", model=_model, tokenizer=_tokenizer)

SKIP_TOKENS = {'.', ',', '!', '?', '[MASK]', ':', '-', '"', "'"}


def get_fill_mask_suggestions(stanza_lines: list[str], target_idx: int, original_word: str, top_k: int = 30) -> list[str]:
    """מחזיר רשימת מילים מוצעות להחלפת original_word בשורה target_idx."""
    masked = list(stanza_lines)
    line = masked[target_idx]
    prefix = line.rsplit(original_word, 1)[0].strip() if original_word in line else line.strip()
    masked[target_idx] = f"{prefix} [MASK]"
    context = " ".join(masked)
    try:
        results = _fill_mask(context, top_k=top_k)
        return [r["token_str"] for r in results if r.get("token_str") and r["token_str"] not in SKIP_TOKENS]
    except Exception:
        return []
