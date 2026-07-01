"""
RhymeChecker — זיהוי חרוז מבוסס ייצוג פונטי.

שלבי העיבוד:
  1. to_phonemes()  — הופך מילה מנוקדת לרצף פונמות מפורש, למשל:
       וְיִרְאָה  →  ['v','i','r','A','']   (A = פתח/קמץ, '' = הא נחה בסוף)
       RA         →  ['r','A']
     כך ניתן להשוות ישירות.
  2. rhyme_phonemes() — מחלץ את פונמות הסיומת לפי הטעמה.
  3. rhyme_level()    — משווה שתי סיומות ומחזיר ציון 1-5.
"""


class RhymeChecker:

    # ---- ניקוד Unicode ----
    SHEVA   = '\u05B0'
    HIRIQ   = '\u05B4'
    TSERE   = '\u05B5'
    SEGOL   = '\u05B6'
    PATAH   = '\u05B7'
    QAMATS  = '\u05B8'
    HOLAM   = '\u05B9'
    QUBUTS  = '\u05BB'
    DAGESH  = '\u05BC'
    HATEF_P = '\u05B2'
    HATEF_S = '\u05B1'
    HATEF_Q = '\u05B3'
    SHINDOT = '\u05C1'
    SINDOT  = '\u05C2'

    # ---- מיפוי ניקוד -> סמל תנועה (מנורמל פונטית) ----
    NIQUD_TO_VOWEL = {
        '\u05B0': '',    # שווא נע — שקט (לא מנורמל לתנועה)
        '\u05B1': 'E',   # חטף סגול
        '\u05B2': 'A',   # חטף פתח
        '\u05B3': 'O',   # חטף קמץ
        '\u05B4': 'I',   # חיריק
        '\u05B5': 'E',   # צרה = סגול פונטית
        '\u05B6': 'E',   # סגול
        '\u05B7': 'A',   # פתח
        '\u05B8': 'A',   # קמץ = פתח פונטית
        '\u05B9': 'O',   # חולם
        '\u05BB': 'U',   # קובוץ/שורוק
    }

    # ---- מיפוי אות עברית -> פונמה (מנורמל) ----
    LETTER_TO_PHONEME = {
        '\u05D0': '',    # אלף — שקט (אם נחה)
        '\u05D1': 'v',   # בית רפה (ללא דגש) = V
        '\u05D2': 'g',
        '\u05D3': 'd',
        '\u05D4': 'h',   # הא — שקט בסוף מילה אם נחה
        '\u05D5': 'v',   # וו רפה = V (שורוק/חולם מטופלים בנפרד)
        '\u05D6': 'z',
        '\u05D7': 'x',   # חת
        '\u05D8': 't',   # טת = ת פונטית
        '\u05D9': 'y',   # יוד (אם לא נחה)
        '\u05DA': 'x',   # כף סופית = ח
        '\u05DB': 'x',   # כף = ח
        '\u05DC': 'l',
        '\u05DD': 'm',
        '\u05DE': 'm',
        '\u05DF': 'n',
        '\u05E0': 'n',
        '\u05E1': 's',
        '\u05E2': '',    # עין — שקט
        '\u05E3': 'p',
        '\u05E4': 'p',
        '\u05E5': 'ts',
        '\u05E6': 'ts',
        '\u05E7': 'k',
        '\u05E8': 'r',
        '\u05E9': 's',   # שין/שין שמאלית — מנורמל ל-s (שין ימנית = sh, אבל לחרוז מספיק)
        '\u05EA': 't',
    }

    # שין ימנית = sh (עם נקודה ימנית)
    # שין שמאלית = s (עם נקודה שמאלית)

    ALL_NIQUD = set(NIQUD_TO_VOWEL) | {DAGESH, SHINDOT, SINDOT}

    # אותיות גרוניות שקדימת פתח גנובה = עבור קצר
    GUTTURALS = {'\u05D0', '\u05D4', '\u05D7', '\u05E2'}

    @classmethod
    def _to_syllables(cls, vocalized_word: str) -> list[tuple[str, str]]:
        """
        הופך מילה מנוקדת לרשימת הברות (phoneme_consonant, phoneme_vowel).
        מטפל בפתח גנובה: פתח (ועוד ניקודים) שמופיעים לפני אות גרונית
        בסוף מילה (ללא ניקוד אחרי הגרונית) סווגים כ-'Ag' (צליל עובר).
        """
        w = vocalized_word.replace('|', '')

        # זיהוי שין ימנית לפני הסרת נקודות
        shin_positions = set()
        for i, c in enumerate(w):
            if c == '\u05E9' and i + 1 < len(w) and w[i+1] == cls.SHINDOT:
                shin_positions.add(i)

        syllables = []
        i = 0
        while i < len(w):
            c = w[i]

            if c in cls.ALL_NIQUD:
                i += 1
                continue

            if '\u05D0' <= c <= '\u05EA':
                # אסוף את הניקוד שאחרי האות
                niqud = []
                j = i + 1
                while j < len(w) and w[j] in cls.ALL_NIQUD:
                    niqud.append(w[j])
                    j += 1

                # בדוק פתח גנובה:
                # תנאי: אות גרונית + פתח בניקוד + אין אחריה תנועה נוספת + זו האות האחרונה במילה
                next_letter_pos = j
                while next_letter_pos < len(w) and w[next_letter_pos] in cls.ALL_NIQUD:
                    next_letter_pos += 1
                is_last_letter = next_letter_pos >= len(w)

                is_patah_ganuvah = (
                    c in cls.GUTTURALS
                    and cls.PATAH in niqud
                    and not any(n in cls.NIQUD_TO_VOWEL and n != cls.PATAH for n in niqud)
                    and is_last_letter
                )

                # המר אות לפונמה
                if c == '\u05E9':
                    cons = 'sh' if i in shin_positions else 's'
                elif c == '\u05D1' and cls.DAGESH in niqud:
                    cons = 'b'
                elif c == '\u05E4' and cls.DAGESH in niqud:
                    cons = 'f'
                elif c == '\u05DB' and cls.DAGESH in niqud:
                    cons = 'k'
                else:
                    cons = cls.LETTER_TO_PHONEME.get(c, c)

                if is_patah_ganuvah:
                    # פתח גנובה: תנועה עוברת קצרה שלא שווה ל-A מלא
                    vowel = 'Ag'  # A-ganuva
                else:
                    vowel = ''
                    for n in niqud:
                        if n in cls.NIQUD_TO_VOWEL:
                            vowel = cls.NIQUD_TO_VOWEL[n]
                            break

                syllables.append((cons, vowel))
                i = j
            else:
                i += 1

        return syllables

    @classmethod
    def _rhyme_tail(cls, syllables: list[tuple[str, str]], stress_type: str) -> list[tuple[str, str]]:
        """
        מחלץ את זנב החרוז מתוך ההברות.
        מלרע: מהתנועה האחרונה בעלת ערך (לא '') ועד הסוף.
        מלעיל: מהתנועה הלפני-אחרונה.
        """
        # מיקומי הברות עם תנועה
        voiced = [i for i, (c, v) in enumerate(syllables) if v != '']

        if not voiced:
            return syllables[-1:] if syllables else []

        if stress_type == 'מלרע':
            start = voiced[-1]
        else:
            start = voiced[-2] if len(voiced) >= 2 else voiced[-1]

        # כלול את ההברה שלפני ה-start (העיצור הנושא)
        start = max(0, start - 1) if start > 0 else start
        return syllables[start:]

    @classmethod
    def extract_rhyme_key(cls, vocalized_word: str, stress_type: str) -> tuple:
        """
        מחזיר מפתח חרוז כ-tuple של (cons, vowel) pairs.
        tuple ניתן להשוואה ישירה.
        """
        syllables = cls._to_syllables(vocalized_word)
        tail = cls._rhyme_tail(syllables, stress_type)
        return tuple(tail)

    @classmethod
    def rhyme_level(cls, key1: tuple, key2: tuple) -> int:
        """
        משווה שני מפתחות חרוז (tuples של פונמות) ומחזיר רמה 1-5.
          1 = חרוז מושלם
          2 = הברה סופית זהה (תנועה + עיצורים סופיים) — עיצור נושא שונה
          3 = עיצורים סופיים זהים, תנועה שונה
          4 = תנועה סופית זהה, עיצורים שונים
          5 = אין חרוז
        """
        if key1 == key2:
            return 1

        def last_vowel(key):
            for cons, vowel in reversed(key):
                if vowel:
                    return vowel
            return ''

        def cons_after_last_vowel(key):
            """רצף העיצורים אחרי התנועה האחרונה."""
            found = False
            result = []
            for cons, vowel in reversed(key):
                if not found:
                    if vowel:
                        found = True
                else:
                    result.append(cons)
            return tuple(reversed(result))

        def last_syllable(key):
            """(תנועה, עיצורים-אחריה)"""
            for i in range(len(key) - 1, -1, -1):
                if key[i][1]:
                    return key[i][1], tuple(c for c, v in key[i+1:] if c)
            return '', ()

        v1, ca1 = last_syllable(key1)
        v2, ca2 = last_syllable(key2)

        if v1 == v2 and ca1 == ca2:   # הברה סופית זהה
            return 2
        if ca1 == ca2 and ca1 != (): # עיצורים סופיים זהים, תנועה שונה
            return 3
        if v1 == v2 and v1 != '':    # תנועה סופית זהה, עיצורים שונים
            return 4
        return 5

    @classmethod
    def analyze_stanza(cls, lines_with_metadata: list[dict]) -> dict:
        """מזהה תבנית חריזה ומפיק דוח התרעות."""

        LEVEL_TYPE = {
            2: 'חרוז טוב',
            3: 'עיצור משותף',
            4: 'תנועה משותפת',
            5: 'חרוז חסר',
        }

        line_keys = [
            cls.extract_rhyme_key(l['last_word_vocalized'], l['stress_type'])
            for l in lines_with_metadata
        ]

        num_lines = len(line_keys)
        if num_lines < 2:
            return {'pattern': 'לא מוגדר', 'alerts': ['הבית קצר מדי'], 'line_keys': line_keys}

        expected_pairs = []
        if num_lines == 4:
            is_aaaa = len(set(line_keys)) == 1
            is_aaab = (line_keys[0] == line_keys[1] == line_keys[2]) and line_keys[2] != line_keys[3]
            score_aabb = (line_keys[0]==line_keys[1]) + (line_keys[2]==line_keys[3])
            score_abab = (line_keys[0]==line_keys[2]) + (line_keys[1]==line_keys[3])
            score_abba = (line_keys[0]==line_keys[3]) + (line_keys[1]==line_keys[2])

            if is_aaaa:
                pattern_name = 'א-א-א-א (חריזה מלאה)'
                expected_pairs = [(0,1),(1,2),(2,3)]
            elif is_aaab:
                pattern_name = 'א-א-א-ב (חריזה פיוטית)'
                expected_pairs = [(0,1),(1,2)]
            elif score_aabb >= score_abab and score_aabb >= score_abba:
                pattern_name = 'א-א-ב-ב (חריזה צמודה)'
                expected_pairs = [(0,1),(2,3)]
            elif score_abba >= score_abab:
                pattern_name = 'א-ב-ב-א (חריזה חובקת)'
                expected_pairs = [(0,3),(1,2)]
            else:
                pattern_name = 'א-ב-א-ב (חריזה מסורגת)'
                expected_pairs = [(0,2),(1,3)]
        else:
            pattern_name = 'חריזה חופשית / אחר'
            expected_pairs = [(i, i+1) for i in range(num_lines-1)]

        alerts = []
        for idx1, idx2 in expected_pairs:
            level = cls.rhyme_level(line_keys[idx1], line_keys[idx2])
            if level == 1:
                continue
            w1 = lines_with_metadata[idx1]['original_word']
            w2 = lines_with_metadata[idx2]['original_word']
            alerts.append({
                'type': LEVEL_TYPE[level],
                'level': level,
                'lines': (idx1+1, idx2+1),
                'message': f'שורה {idx1+1} ({w1}) ושורה {idx2+1} ({w2}): {LEVEL_TYPE[level]}.'
            })

        return {'pattern': pattern_name, 'alerts': alerts, 'line_keys': line_keys, 'expected_pairs_indices': expected_pairs}
