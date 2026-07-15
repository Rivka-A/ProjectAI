"""
RhymeChecker — מנוע פונטי אחוד לזיהוי, דירוג, סינון וניתוח חריזה.
מקור האמת היחיד (Single Source of Truth) לפרויקט.
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
        '\u05E9': 's',   # שין/שין שמאלית — מנורמל ל-s
        '\u05EA': 't',
    }

    ALL_NIQUD = set(NIQUD_TO_VOWEL) | {DAGESH, SHINDOT, SINDOT}

    # הגדרת קבוצות מוצא פונטיות
    source = {
        'GUTTURALS': {'', 'h', 'x'},           # א (שקטה), ה, ח/כ רפה, ע (שקטה)
        'LINGUISTIC': {'d', 't', 'l', 'n'},    # ד, ט, ל, נ, ת
        'TEETHING': {'z', 's', 'ts', 'sh'},    # ז, ס, צ, ש
        'PALATAL': {'g', 'y', 'x', 'k', 'r'},  # ג, י, כ, ק, ר
        'LIPS': {'v', 'b', 'm', 'p', 'f'}      # ב, ו, מ, פ
    }

    # משקל לכל רמת חריזה: ככל שהחריזה טובה יותר (רמה נמוכה) - משקל גבוה יותר.
    # משמש לקביעת מבנה חריזה (analyze_stanza) לפי דירוג מדורג ולא סף בינארי.
    LEVEL_WEIGHT = {1: 4, 2: 3, 3: 2, 4: 1, 5: 0}

    @classmethod
    def _to_syllables(cls, vocalized_word: str) -> list[tuple[str, str]]:
        """הופך מילה מנוקדת לרשימת הברות (phoneme_consonant, phoneme_vowel)."""
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
                niqud = []
                j = i + 1
                while j < len(w) and w[j] in cls.ALL_NIQUD:
                    niqud.append(w[j])
                    j += 1

                # בדוק פתח גנובה
                next_letter_pos = j
                while next_letter_pos < len(w) and w[next_letter_pos] in cls.ALL_NIQUD:
                    next_letter_pos += 1
                is_last_letter = next_letter_pos >= len(w)

                is_patah_ganuvah = (
                    c in cls.source['GUTTURALS']
                    and cls.PATAH in niqud
                    and not any(n in cls.NIQUD_TO_VOWEL and n != cls.PATAH for n in niqud)
                    and is_last_letter
                )

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
                    vowel = 'Ag'
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
        """מחלץ את זנב החרוז מתוך ההברות."""
        voiced = [i for i, (c, v) in enumerate(syllables) if v != '']

        if not voiced:
            return syllables[-1:] if syllables else []

        if stress_type == 'מלרע':
            start = voiced[-1]
        else:
            start = voiced[-2] if len(voiced) >= 2 else voiced[-1]

        start = max(0, start - 1) if start > 0 else start
        return syllables[start:]

    @classmethod
    def extract_rhyme_key(cls, vocalized_word: str, stress_type: str) -> tuple:
        """מחזיר מפתח חרוז פונטי כ-tuple של זוגות (עיצור, תנועה)."""
        syllables = cls._to_syllables(vocalized_word)
        tail = cls._rhyme_tail(syllables, stress_type)
        return tuple(tail)

    @classmethod
    def rhyme_level(cls, key1: tuple, key2: tuple) -> int:
        """
        מחזיר ציון רמת חריזה בין 1 ל-5:
        1 = חרוז מושלם    (כל המפתח זהה)
        2 = חרוז טוב      (תנועה + עיצורים סופיים זהים, עיצור נושא באותה קבוצה)
        3 = עיצור משותף   (תנועה זהה, עיצורים סופיים שונים באותה קבוצה)
        4 = תנועה משותפת  (תנועה זהה, ללא עיצורים חוסמים בסוף - אסונאנס פתוח)
        5 = לא חרוז
        """
        if key1 == key2:
            return 1

        # פונקציית עזר פנימית לחילוץ בטוח
        def analyze_key(key):
            onset = ''
            vowel = ''
            coda = ()

            if not key:
                return onset, vowel, coda

            for i in range(len(key) - 1, -1, -1):
                c, v = key[i]
                if v != '':
                    onset = c
                    vowel = v
                    # ה-Coda מנוקה מ-h שקטה בסוף המילה
                    coda = tuple(char for char, vow in key[i+1:] if char and char != 'h')
                    return onset, vowel, coda
            return onset, vowel, coda

        onset1, v1, coda1 = analyze_key(key1)
        onset2, v2, coda2 = analyze_key(key2)

        # אם אין תנועה מוטעמת או שהתנועות שונות - פוסל מיד
        if not v1 or not v2 or v1 != v2:
            return 5

        # --- דרגה 4 (אסונאנס פתוח) ---
        # אם שתי המילים מסתיימות בתנועה פתוחה וזהה (ללא קודה חוסמת)
        # הן מוגדרות מיד כדרגה 4, ללא תלות בקבוצת ה-Onset! (למשל: גיתה ומשפחה)
        if not coda1 and not coda2:
            return 4

        # פונקציית עזר לקבלת קבוצת המוצא הפונטית של עיצור
        def get_group(c):
            if not c:
                return 'GUTTURALS'
            for name, phonemes in cls.source.items():
                if c in phonemes:
                    return name
            return None

        onset_group1 = get_group(onset1)
        onset_group2 = get_group(onset2)

        # בדרגות 2 ו-3, אנחנו כן דורשים שהעיצורים הנושאים (Onset) יהיו מאותה קבוצה
        if onset_group1 != onset_group2:
            return 5

        # --- דרגה 2 (עיצורים סופיים זהים) ---
        if coda1 == coda2:
            return 2

        # --- דרגה 3 (עיצורים סופיים שונים אך מאותה קבוצה פונטית) ---
        if len(coda1) == len(coda2) and len(coda1) > 0:
            if all(
                get_group(c1) == get_group(c2) and get_group(c1) is not None
                for c1, c2 in zip(coda1, coda2)
            ):
                return 3

        return 5

    # =========================================================================
    #               לוגיקות סינון, דירוג וניתוח (ממוזגות מה-Improved)
    # =========================================================================

    @classmethod
    def is_valid_rhyme(cls, word1: str, word2: str, stress1: str, stress2: str, min_level: int = 2) -> bool:
        """בוחן האם שתי מילים מנוקדות מתחרזות ברמת סף מסוימת ומעלה."""
        key1 = cls.extract_rhyme_key(word1, stress1)
        key2 = cls.extract_rhyme_key(word2, stress2)

        level = cls.rhyme_level(key1, key2)
        return level <= min_level

    @classmethod
    def filter_suggestions_by_rhyme(cls, suggestions: list[str], target_word: str,
                                    target_stress: str, min_level: int = 2,
                                    vocalize_fn=None, detect_stress_fn=None) -> list[str]:
        """
        מסנן רשימת מילים מוצעות ומחזיר רק את אלו שמתחרזות ברמה הנדרשת ומעלה.
        vocalize_fn ו-detect_stress_fn מוזרקים מבחוץ למניעת ייבוא מעגלי.
        """
        if not vocalize_fn or not detect_stress_fn:
            raise ValueError("יש להזריק פונקציות ניקוד וזיהוי הטעמה למניעת ייבוא מעגלי.")

        filtered = []
        target_key = cls.extract_rhyme_key(target_word, target_stress)

        for sug in suggestions:
            try:
                voc = vocalize_fn(sug)
                stress = detect_stress_fn(voc)
                sug_key = cls.extract_rhyme_key(voc, stress)

                level = cls.rhyme_level(target_key, sug_key)
                if level <= min_level:
                    filtered.append(sug)
            except Exception:
                continue
        return filtered

    @classmethod
    def rank_suggestions_by_rhyme_quality(cls, suggestions: list[str], target_word: str,
                                          target_stress: str, vocalize_fn=None,
                                          detect_stress_fn=None) -> list[tuple[str, int]]:
        """מדרג רשימת מילים מוצעות ומחזיר רשימה של טאפלים (מילה, רמת_חריזה) ממוינת מהטוב ביותר."""
        if not vocalize_fn or not detect_stress_fn:
            raise ValueError("יש להזריק פונקציות ניקוד וזיהוי הטעמה למניעת ייבוא מעגלי.")

        ranked = []
        target_key = cls.extract_rhyme_key(target_word, target_stress)

        for sug in suggestions:
            try:
                voc = vocalize_fn(sug)
                stress = detect_stress_fn(voc)
                sug_key = cls.extract_rhyme_key(voc, stress)

                level = cls.rhyme_level(target_key, sug_key)
                if level <= 4:  # חוקי לחריזה כלשהי
                    ranked.append((sug, level))
            except Exception:
                continue

        ranked.sort(key=lambda x: x[1])
        return ranked

    @classmethod
    def _pattern_score(cls, levels: list[int]) -> float:
        """
        ציון ממוצע מדורג לפי משקלות הרמות (LEVEL_WEIGHT), ולא ספירה בינארית
        של "מתחרז/לא מתחרז". תבנית עם חרוזים ברמה טובה יותר תקבל ציון גבוה יותר
        גם אם שתי התבניות היו "עוברות סף" בבדיקה בינארית.
        """
        if not levels:
            return 0.0
        return sum(cls.LEVEL_WEIGHT.get(l, 0) for l in levels) / len(levels)

    @classmethod
    def analyze_stanza(cls, lines_with_metadata: list[dict]) -> dict:
        """מנתח בית של שיר ומזהה תבניות חריזה, כולל הפקת דוחות והתרעות."""
        LEVEL_TYPE = {
            1: 'חרוז מושלם',
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
            # רמות החריזה בפועל לכל זוג שורות אפשרי - נבדק פעם אחת ומשמש לכל השאר
            l01 = cls.rhyme_level(line_keys[0], line_keys[1])
            l12 = cls.rhyme_level(line_keys[1], line_keys[2])
            l23 = cls.rhyme_level(line_keys[2], line_keys[3])
            l02 = cls.rhyme_level(line_keys[0], line_keys[2])
            l13 = cls.rhyme_level(line_keys[1], line_keys[3])
            l03 = cls.rhyme_level(line_keys[0], line_keys[3])

            # AAAB: מקרה אסימטרי מיוחד - 3 השורות הראשונות מתחרזות היטב,
            # הרביעית שונה בכוונה (אין לה זוג). נבדק פונטית (<=2) ולא בשוויון מדויק (==).
            is_aaab = l01 <= 2 and l12 <= 2 and l23 >= 4
            is_aaaa = cls._pattern_score([l01, l12, l23]) == cls.LEVEL_WEIGHT[1]  # כל הזוגות ברמה 1

            if is_aaaa:
                pattern_name = 'א-א-א-א (חריזה מלאה)'
                expected_pairs = [(0, 1), (1, 2), (2, 3)]
            elif is_aaab:
                pattern_name = 'א-א-א-ב (חריזה פיוטית)'
                expected_pairs = [(0, 1), (1, 2)]
            else:
                candidates = {
                    'א-א-ב-ב (חריזה צמודה)':  (cls._pattern_score([l01, l23]), [(0, 1), (2, 3)]),
                    'א-ב-א-ב (חריזה מסורגת)': (cls._pattern_score([l02, l13]), [(0, 2), (1, 3)]),
                    'א-ב-ב-א (חריזה חובקת)':  (cls._pattern_score([l03, l12]), [(0, 3), (1, 2)]),
                }
                best_name, (best_score, best_pairs) = max(candidates.items(), key=lambda kv: kv[1][0])

                if best_score == 0:
                    # אף זוג לא מתחרז באף רמה - אין לכפות תבנית שרירותית
                    pattern_name = 'חופשית / לא זוהתה תבנית'
                    expected_pairs = []
                else:
                    pattern_name = best_name
                    expected_pairs = best_pairs
        else:
            pattern_name = 'חריזה חופשית / אחר'
            expected_pairs = [(i, i + 1) for i in range(num_lines - 1)]

        alerts = []
        for idx1, idx2 in expected_pairs:
            level = cls.rhyme_level(line_keys[idx1], line_keys[idx2])
            if level == 1:
                continue
            w1 = lines_with_metadata[idx1].get('original_word', 'מילה א')
            w2 = lines_with_metadata[idx2].get('original_word', 'מילה ב')

            alert_name = LEVEL_TYPE.get(level, 'חרוז חסר')
            alerts.append({
                'type': alert_name,
                'level': level,
                'lines': (idx1+1, idx2+1),
                'message': f'שורה {idx1+1} ({w1}) ושורה {idx2+1} ({w2}): {alert_name}.'
            })

        return {
            'pattern': pattern_name,
            'alerts': alerts,
            'line_keys': line_keys,
            'expected_pairs_indices': expected_pairs
        }