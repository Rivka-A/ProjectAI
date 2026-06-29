class RhymeChecker:

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

    VOWELS = {'\u05B0','\u05B4','\u05B5','\u05B6','\u05B7','\u05B8','\u05B9','\u05BB'}

    @classmethod
    def _normalize(cls, word):
        """ניקוי דגש, מפרידים, ונרמול תנועות שוות-ערך."""
        w = word.replace('|', '').replace(cls.DAGESH, '')
        w = w.replace(cls.HATEF_P, cls.PATAH)
        w = w.replace(cls.HATEF_S, cls.SEGOL)
        w = w.replace(cls.HATEF_Q, cls.HOLAM)
        w = w.replace(cls.QAMATS,  cls.PATAH)
        w = w.replace(cls.TSERE,   cls.SEGOL)
        return w

    @classmethod
    def _phonetic_consonants(cls, text):
        """החלפת עיצורים הנשמעים זהה."""
        MAP = {'\u05D8':'\u05EA', '\u05DB':'\u05D7', '\u05E7':'\u05DB', '\u05E1':'\u05E9', '\u05D0':'\u05E2'}
        return ''.join(MAP.get(c, c) for c in text)

    @classmethod
    def _absorb_matres(cls, word):
        """
        מסיר אמות קריאה נחות (א/ה/ו/י שאחרי תנועה ולפניהן אין ניקוד).
        כך "מָצָא" ו"מְנוּחָה" יקבלו אותה תנועה סופית.
        """
        MATRES = {'\u05D0', '\u05D4', '\u05D5', '\u05D9'}
        chars = list(word)
        result = []
        i = 0
        while i < len(chars):
            c = chars[i]
            if c in MATRES:
                prev_is_vowel = result and result[-1] in cls.VOWELS
                next_is_niqud = (i + 1 < len(chars)) and (chars[i+1] in cls.VOWELS)
                if prev_is_vowel and not next_is_niqud:
                    i += 1
                    continue
            result.append(c)
            i += 1
        return ''.join(result)

    @classmethod
    def extract_rhyme_key(cls, vocalized_word, stress_type):
        """
        מחלץ את מפתח החרוז: העיצור הנושא + תנועה מוטעמת + כל מה שאחריה.
        כך 'סָּע' ו-'רַע' יקבלו מפתחות שונים גם אם שניהם מסתיימים ב-ע.
        """
        w = cls._normalize(vocalized_word)
        w = cls._absorb_matres(w)
        w = cls._phonetic_consonants(w)

        vowel_indices = [i for i, c in enumerate(w) if c in cls.VOWELS]
        if not vowel_indices:
            return w[-2:] if len(w) >= 2 else w

        if stress_type == '\u05DE\u05DC\u05E8\u05E2':
            stressed_vowel_pos = vowel_indices[-1]
        else:
            stressed_vowel_pos = vowel_indices[-2] if len(vowel_indices) >= 2 else vowel_indices[0]

        # מוצאים את העיצור הנושא (האות שלפני התנועה המוטעמת)
        cons_pos = stressed_vowel_pos - 1
        while cons_pos >= 0 and w[cons_pos] in cls.VOWELS:
            cons_pos -= 1

        start = max(0, cons_pos)
        return w[start:]

    @classmethod
    def rhyme_level(cls, key1, key2):
        """
        מחזיר רמת חרוז בין שני מפתחות.
        כל מפתח = עיצור_נושא + תנועה + עיצורים_סופיים.
        ההשוואה מבוססת על ההברה הסופית (תנועה + עיצורים אחריה) בלבד:
          1 = חרוז מושלם (מפתחות זהים לחלוטין)
          2 = הברה סופית זהה: תנועה זהה + עיצורים סופיים זהים (עיצור נושא יכול להשתנות)
          3 = עיצורים סופיים זהים, תנועה שונה
          4 = תנועה סופית זהה, עיצורים סופיים שונים
          5 = אין חרוז
        """
        if key1 == key2:
            return 1

        IS_HEB = lambda c: '\u05D0' <= c <= '\u05EA'

        def parse_key(key):
            """מחזיר (last_vowel, consonants_after_last_vowel)"""
            vpos = [i for i, c in enumerate(key) if c in cls.VOWELS]
            if not vpos:
                letters = [c for c in key if IS_HEB(c)]
                return '', letters[-1] if letters else ''
            lv = vpos[-1]
            return key[lv], ''.join(c for c in key[lv+1:] if IS_HEB(c))

        v1, ca1 = parse_key(key1)
        v2, ca2 = parse_key(key2)

        if v1 == v2 and ca1 == ca2:
            return 2
        if ca1 == ca2 and ca1 != '':
            return 3
        if v1 == v2 and v1 != '':
            return 4
        return 5

    @classmethod
    def analyze_stanza(cls, lines_with_metadata):
        """מזהה תבנית חריזה ומפיק דוח התרעות עם 5 רמות חרוז."""

        LEVEL_TYPE = {
            2: '\u05D7\u05E8\u05D5\u05D6 \u05D8\u05D5\u05D1',
            3: '\u05E2\u05D9\u05E6\u05D5\u05E8 \u05DE\u05E9\u05D5\u05EA\u05E3',
            4: '\u05EA\u05E0\u05D5\u05E2\u05D4 \u05DE\u05E9\u05D5\u05EA\u05E4\u05EA',
            5: '\u05D7\u05E8\u05D5\u05D6 \u05D7\u05E1\u05E8',
        }

        line_keys = [
            cls.extract_rhyme_key(l['last_word_vocalized'], l['stress_type'])
            for l in lines_with_metadata
        ]

        num_lines = len(line_keys)
        if num_lines < 2:
            return {'pattern': '\u05DC\u05D0 \u05DE\u05D5\u05D2\u05D3\u05E8', 'alerts': ['\u05D4\u05D1\u05D9\u05EA \u05E7\u05E6\u05E8 \u05DE\u05D3\u05D9'], 'line_keys': line_keys}

        expected_pairs = []
        if num_lines == 4:
            is_aaaa = len(set(line_keys)) == 1
            is_aaab = (line_keys[0] == line_keys[1] == line_keys[2]) and line_keys[2] != line_keys[3]
            score_aabb = (line_keys[0]==line_keys[1]) + (line_keys[2]==line_keys[3])
            score_abab = (line_keys[0]==line_keys[2]) + (line_keys[1]==line_keys[3])
            score_abba = (line_keys[0]==line_keys[3]) + (line_keys[1]==line_keys[2])

            if is_aaaa:
                pattern_name = '\u05D0-\u05D0-\u05D0-\u05D0 (\u05D7\u05E8\u05D9\u05D6\u05D4 \u05DE\u05DC\u05D0\u05D4)'
                expected_pairs = [(0,1),(1,2),(2,3)]
            elif is_aaab:
                pattern_name = '\u05D0-\u05D0-\u05D0-\u05D1 (\u05D7\u05E8\u05D9\u05D6\u05D4 \u05E4\u05D9\u05D5\u05D8\u05D9\u05EA)'
                expected_pairs = [(0,1),(1,2)]
            elif score_abab >= score_aabb and score_abab >= score_abba:
                pattern_name = '\u05D0-\u05D1-\u05D0-\u05D1 (\u05D7\u05E8\u05D9\u05D6\u05D4 \u05DE\u05E1\u05D5\u05E8\u05D2\u05EA)'
                expected_pairs = [(0,2),(1,3)]
            elif score_abba >= score_aabb:
                pattern_name = '\u05D0-\u05D1-\u05D1-\u05D0 (\u05D7\u05E8\u05D9\u05D6\u05D4 \u05D7\u05D5\u05D1\u05E7\u05EA)'
                expected_pairs = [(0,3),(1,2)]
            else:
                pattern_name = '\u05D0-\u05D0-\u05D1-\u05D1 (\u05D7\u05E8\u05D9\u05D6\u05D4 \u05E6\u05DE\u05D5\u05D3\u05D4)'
                expected_pairs = [(0,1),(2,3)]
        else:
            pattern_name = '\u05D7\u05E8\u05D9\u05D6\u05D4 \u05D7\u05D5\u05E4\u05E9\u05D9\u05EA / \u05D0\u05D7\u05E8'
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
                'message': f'\u05E9\u05D5\u05E8\u05D4 {idx1+1} ({w1}) \u05D5\u05E9\u05D5\u05E8\u05D4 {idx2+1} ({w2}): {LEVEL_TYPE[level]}.'
            })

        return {'pattern': pattern_name, 'alerts': alerts, 'line_keys': line_keys}
