VOWELS_SET = set("אבגדהוזחטיכלמנסעפצקרשתךםןףץ")

def extract_rhyme_ending(word: str, n: int = 3) -> str:
    """מחלץ את n התווים האחרונים של המילה (ללא ניקוד) לצורך השוואת חריזה."""
    clean = "".join(ch for ch in word if '\u05D0' <= ch <= '\u05EA')
    return clean[-n:] if len(clean) >= n else clean

def check_rhyme_pattern(lines: list[str], pattern: str = "AABB") -> list[str]:
    """
    בודק אם שורות השיר עומדות בתבנית חריזה נתונה.
    מחזיר רשימת התרעות על שורות שאינן חורזות כנדרש.
    pattern: מחרוזת כגון 'AABB', 'ABAB', 'ABBA'
    """
    warnings = []
    rhyme_map = {}  # אות תבנית -> סיומת חרוז

    for i, line in enumerate(lines):
        if i >= len(pattern):
            break
        words = line.split()
        if not words:
            continue
        last_word = words[-1]
        ending = extract_rhyme_ending(last_word)
        label = pattern[i]

        if label not in rhyme_map:
            rhyme_map[label] = ending
        elif rhyme_map[label] != ending:
            warnings.append(
                f"שורה {i+1}: מצופה חרוז '{rhyme_map[label]}' אך נמצא '{ending}'"
            )

    return warnings
