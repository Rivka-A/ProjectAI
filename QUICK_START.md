# מתקן השירים האוטומטי

כלי לניתוח חריזה בשירים עבריים והצעת שיפורים באמצעות מודל שפה (BERT).

## התקנה פרוט הסיפריות מצורף בהמשך

```bash
pip install requests
pip install transformers
pip install torch
pip install sentencepiece
pip install protobuf
pip install streamlit
pip install pytest

```

## הרצת הפרויקט

```bash
streamlit run UI/app.py
```

## ספריות נדרשות

| ספרייה | גרסה מינימלית | שימוש |
|--------|--------------|-------|
| `streamlit` | — | ממשק משתמש |
| `requests` | — | תקשורת עם שירות הניקוד (Nakdan) |
| `urllib3` | — | ביטול אזהרות SSL |
| `torch` |  הרצת מודל BERT |
| `transformers`  | טעינת מודל BERT (`AutoTokenizer`, `AutoModelForMaskedLM`, `pipeline`) |
| `numpy` | `<2` | תלות של torch (חייב להיות מתחת ל-2) |
| `sentencepiece` | — | תלות של transformers |
| `protobuf` | — | תלות של transformers |

### פקודת התקנה מלאה

```bash
pip install streamlit requests urllib3 "torch>=2.0.0" "transformers>=4.30.0" "numpy<2" sentencepiece protobuf
```

## מודל מקומי

המודל `avichr/heBERT` נטען מהתיקייה `moduls/` (ללא גישה לאינטרנט).  
הקבצים הנדרשים בתיקייה:

```
moduls/
├── config.json
├── pytorch_model.bin
├── tokenizer_config.json
└── vocab.txt
```

## שירות ניקוד

האפליקציה משתמשת ב-API של [Nakdan Dicta](https://nakdan.dicta.org.il/) לניקוד מילים.  
נדרש חיבור לאינטרנט לשירות זה.
