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
        
        # 1. ניקוי מפרידים ודגשים לצורך ניתוח נקי
        clean_word = vocalized_word.replace("|", "").replace("ּ", "")
        
        # 2. חוק הסגוליים הכללי (למשל 'חֶלֶד', או 'בַּנֶּגֶב')
        if clean_word.count(segol) >= 2:
            return "מלעיל"
            
        # 3. חוק מילים מיוחדות בסיומת סגול-הא שהן מלעיל (כמו אֵלֶּה, לָמָּה)
        if clean_word.endswith(segol + 'ה'):
            if tsere in clean_word or clean_word.count(segol) >= 2:
                return "מלעיל"
                
        # 4. החוק המדויק שלך: בדיקת האות הלפני-אחרונה במילים עם סיומת קמץ-הא
        if clean_word.endswith(qamats + 'ה'):
            
            # נפרק את המילה לקבוצות של [אות + הניקוד שלה] מתחילת המילה ועד סופה
            letters_with_niqud = []
            current_cluster = ""
            
            for char in clean_word:
                # אם התו הוא אות עברית (בין א' ל-ת')
                if '\u05D0' <= char <= '\u05EA':
                    if current_cluster:
                        letters_with_niqud.append(current_cluster)
                    current_cluster = char
                else:
                    # זהו תו ניקוד, נצמיד אותו לאות שלו
                    current_cluster += char
            if current_cluster:
                letters_with_niqud.append(current_cluster)
            
            # עכשיו יש לנו רשימה נקייה שבה כל איבר הוא אות מנוקדת. 
            # למשל עבור "לַיְלָה": ['לַ', 'יְ', 'לָ', 'ה']
            # למשל עבור "הַצְלָחָה": ['הַ', 'צְ', 'לָ', 'חָ', 'ה']
            if len(letters_with_niqud) >= 3:
                # האות האחרונה היא ה' (אינדקס 1-)
                # האות הלפני-אחרונה היא העיצור שלפני ההא (אינדקס 2-) -> ב'בננה' או 'הצלחה' זו האות עם הקמץ של הסוף
                # האות שקודמת לה (ההברה הלפני-אחרונה באוזן) היא אינדקס 3- מהסוף!
                before_last_vowel_letter = letters_with_niqud[-3]
                
                # הכלל שלך: במילים כמו לַיְלָה וּבַיְתָה, האות הזו חייבת להכיל שווא!
                if sheva in before_last_vowel_letter:
                    # ונוודא שבאות הראשונה של המילה יש תנועה קטנה כמו פתח שמחזיקה את המלעיל
                    if patach in letters_with_niqud[0]:
                        return "מלעיל"

        # ברירת המחדל הרחבה בעברית היא מלרע
        return "מלרע"