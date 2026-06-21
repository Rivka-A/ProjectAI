import streamlit as st
import sys
import os

# חיבור נתיב השורש כדי שיוכל לייבא את ה-pipeline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import process_and_fix_poem_pipeline

st.set_page_config(page_title="מתקן השירים האוטומטי", layout="centered")
st.title("✨ מתקן השירים האוטומטי")
st.write("הדביקי שיר חופשי. ה-Core ינתח חריזה, ה-Target (דיקטא) יתקן, והכול יתעדכן דינמית.")

# אתחול משתני ה-Session State במידה ואינם קיימים
if "suggestion_index" not in st.session_state:
    st.session_state.suggestion_index = 0

def on_poem_change():
    """ פונקציית אירוע קריטית: ברגע שיש שינוי בטקסט, מאפסים מיד את הדירוגים ל-0 """
    st.session_state.suggestion_index = 0

# תיבת קלט חופשית המחוברת לפונקציית האיפוס בזמן אמת
user_poem = st.text_area(
    "✍️ הדביקי כאן את השיר שלך (רווח של שורה ריקה בין בית לבית):", 
    height=200,
    key="current_poem_input",
    on_change=on_poem_change
)

if user_poem:
    # הפעלת הצינור המנתב
    with st.spinner("🔄 המערכת מנתחת חריזה ומעדכנת סיווגים דינמיים..."):
        full_poem_html, has_replacements = process_and_fix_poem_pipeline(
            user_poem, 
            rank=st.session_state.suggestion_index
        )
    
    st.subheader("✨ השיר והסיווגים המעודכנים:")
    st.markdown(full_poem_html, unsafe_allow_html=True)
    
    if has_replacements:
        st.write("---")
        st.write(f"📊 **האם את מרוצה מהתיקון האוטומטי? (מציג כעת חלופה מספר {st.session_state.suggestion_index + 1}):**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 כן, אני מרוצה"):
                st.success("מעולה! התיקון נשמר.")
                st.session_state.suggestion_index = 0
        with col2:
            if st.button("🔄 לא, הציעו לי מילה אחרת"):
                st.session_state.suggestion_index += 1
                st.rerun()