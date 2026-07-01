"""
קונפיגורציה למערכת BERT המשופרת.
"""

# מודלים
MODELS = {
    'hebert': {
        'name': 'avichr/heBERT',
        'type': 'masked-lm',
        'language': 'Hebrew',
        'description': 'BERT model trained on Hebrew text'
    },
    'mt5': {
        'name': 'google/mt5-small',
        'type': 'seq2seq',
        'language': 'Multilingual',
        'description': 'Multilingual T5 for text generation'
    }
}

# פרמטרים
PARAMETERS = {
    'fill_mask': {
        'top_k': 30,
        'max_length': 512,
    },
    'text_generation': {
        'max_length': 25,
        'num_beams': 3,
        'temperature': 0.7,
    },
    'sentence_completion': {
        'min_word_length': 2,
        'max_suggestions': 5,
    }
}

# סיומות עברי נפוצות
HEBREW_ENDINGS = {
    'verb': ['ים', 'ות', 'ה', 'י', 'ו', 'ן', 'ת'],
    'noun': ['ים', 'ות', 'ה', 'י', 'ו', 'ן', 'ת', 'ית'],
    'adjective': ['ים', 'ות', 'ה', 'י'],
}

# דפוסים דקדוקיים
GRAMMAR_PATTERNS = {
    'masculine_plural': 'ים',
    'feminine_plural': 'ות',
    'feminine_singular': 'ה',
    'construct_state': 'י',
}

# הגדרות ביצועים
PERFORMANCE = {
    'use_gpu': True,
    'batch_size': 1,
    'cache_models': True,
    'timeout': 30,  # שניות
}

# הגדרות logging
LOGGING = {
    'level': 'INFO',
    'file': 'hebrew_nlp.log',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}
