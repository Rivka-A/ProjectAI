
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM
MODEL_PATH = r"C:\Users\user\ProjectAI\moduls"

print("🔄 טוען את DictaBERT...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True,
    use_fast=False
)

model = AutoModelForMaskedLM.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model.eval()

print("✅ DictaBERT נטען בהצלחה")
def query_dicta_bert_api(stanza_lines, target_line_idx, original_word):
    """
    מחזירה הצעות סמנטיות ממודל DictaBERT מקומי.
    """

    try:
        masked_lines = list(stanza_lines)

        current_line = masked_lines[target_line_idx]

        line_without_last_word = (
            current_line.rsplit(original_word, 1)[0].strip()
        )

        masked_lines[target_line_idx] = (
            f"{line_without_last_word} [MASK]"
        )

        context_text = " ".join(masked_lines)

        inputs = tokenizer(
            context_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        mask_token_index = (
            inputs["input_ids"][0] == tokenizer.mask_token_id
        ).nonzero(as_tuple=True)[0]

        if len(mask_token_index) == 0:
            return []

        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits

        mask_logits = logits[
            0,
            mask_token_index[0],
            :
        ]

        top_tokens = torch.topk(
            mask_logits,
            5
        )

        suggestions = []

        for token_id, score in zip(
            top_tokens.indices,
            top_tokens.values
        ):

            word = tokenizer.decode(
                [token_id]
            ).strip()

            if (
                word
                and word != "[MASK]"
                and len(word) > 1
            ):
                suggestions.append(
                    {
                        "word": word,
                        "confidence_score":
                            round(float(score), 2)
                    }
                )

        return suggestions

    except Exception as e:
        print(f"❌ שגיאה במודל המקומי: {e}")
        return []
# if __name__ == "__main__":
#     run_rhyme_ai_assistant(DATASET_PATH)