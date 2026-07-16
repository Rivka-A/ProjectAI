class StressDetector:
    @staticmethod
    def detect_stress(vocalized_word):
        """
        מזהה הטעמה בעברית על בסיס מיקומי תנועות ושוואים מדויקים.
        """
        sheva = '\u05B0'
        segol = '\u05B6'
        tsere = '\u05B5'
        qamats = '\u05B8'
        patach = '\u05B7'
        hiriq = '\u05B4'
        holam = '\u05B9'
        qubuts = '\u05BB'
        yod = '\u05D9'

        # 1. ניקוי מפרידים ודגשים לצורך ניתוח נקי
        clean_word = vocalized_word.replace("|", "").replace("ּ", "")

        # 2. חוק הסגוליים הכללי (למשל 'חֶלֶד', או 'בַּנֶּגֶב')
        if clean_word.count(segol) >= 2:
            return "מלעיל"

        # 3. חוק מילים מיוחדות בסיומת סגול-הא שהן מלעיל (כמו אֵלֶּה, לָמָּה)
        if clean_word.endswith(segol + 'ה'):
            if tsere in clean_word or clean_word.count(segol) >= 2:
                return "מלעיל"

        # פירוק המילה לרשימת [אות + הניקוד שלה], משמש גם לחוק 4 וגם לחוק 5
        letters_with_niqud = []
        current_cluster = ""
        for char in clean_word:
            if '\u05D0' <= char <= '\u05EA':
                if current_cluster:
                    letters_with_niqud.append(current_cluster)
                current_cluster = char
            else:
                current_cluster += char
        if current_cluster:
            letters_with_niqud.append(current_cluster)

        # 4. החוק המדויק שלך: בדיקת האות הלפני-אחרונה במילים עם סיומת קמץ-הא
        if clean_word.endswith(qamats + 'ה'):
            # למשל עבור "לַיְלָה": ['לַ', 'יְ', 'לָ', 'ה']
            # למשל עבור "הַצְלָחָה": ['הַ', 'צְ', 'לָ', 'חָ', 'ה']
            if len(letters_with_niqud) >= 3:
                # האות הלפני-אחרונה היא העיצור שלפני ההא
                # האות שקודמת לה (ההברה הלפני-אחרונה באוזן) היא אינדקס 3- מהסוף
                before_last_vowel_letter = letters_with_niqud[-3]

                # הכלל שלך: במילים כמו לַיְלָה וּבַיְתָה, האות הזו חייבת להכיל שווא!
                if sheva in before_last_vowel_letter:
                    # ונוודא שבאות הראשונה של המילה יש תנועה קטנה כמו פתח שמחזיקה את המלעיל
                    if patach in letters_with_niqud[0]:
                        return "מלעיל"

        # 5. חוק הסגוליים מסוג "דיפתונג עם יו"ד גולשת" (בַּיִת, זַיִת, קַיִץ, אַיִל...)
        # תבנית: עיצור+תנועה פתוחה (פתח/סגול/צירה), יו"ד+חיריק (הדיפתונג ay נכתב עם חיריק
        # תחת היו"ד), עיצור סופי ללא תנועה משלו. ההטעמה נשארת על ההברה הראשונה (מלעיל),
        # למרות שהאות האחרונה בפועל בעלת "תנועה מלאה" (חיריק) - זה מה שמבדיל את "בית"
        # ממקרה כמו "שַׂקִּית" (שם האות האמצעית היא ק' ולא יו"ד, ולכן ההטעמה מלרעית כרגיל).
        if not clean_word.endswith('ה') and len(letters_with_niqud) >= 3:
            first_letter, second_letter, last_letter = (
                letters_with_niqud[-3], letters_with_niqud[-2], letters_with_niqud[-1]
            )

            full_vowels = (patach, qamats, segol, tsere, hiriq, holam, qubuts)

            second_is_yod_with_hiriq = second_letter.startswith(yod) and hiriq in second_letter
            first_has_open_vowel = any(v in first_letter for v in (patach, segol, tsere))
            last_has_no_vowel = not any(v in last_letter for v in full_vowels)

            if second_is_yod_with_hiriq and first_has_open_vowel and last_has_no_vowel:
                return "מלעיל"

        return "מלרע"