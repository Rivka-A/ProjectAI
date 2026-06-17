class StressDetector:
    @staticmethod
    def detect_stress(vocalized_word):
        # ניקוי תווים מפרידים אם קיימים
        clean_word = vocalized_word.replace("|", "")
        
        # תווי יוניקוד של הניקוד בעברית
        segol = '\u05B6'
        qamats = '\u05B8'
        
        # בדיקת משקל סגולי (שני סגולים רצופים לקראת סוף המילה)
        if clean_word.count(segol) >= 2:
            last_segol_idx = clean_word.rfind(segol)
            prev_segol_idx = clean_word.rfind(segol, 0, last_segol_idx)
            if last_segol_idx - prev_segol_idx <= 3:
                return "מלעיל"
                
        # בדיקת סיומת קמץ-הא (כמו לָמָּה)
        if clean_word.endswith(qamats + 'ה') or clean_word.endswith('ת' + qamats):
            return "מלעיל"
            
        # ברירת מחדל בעברית
        return "מלרע"