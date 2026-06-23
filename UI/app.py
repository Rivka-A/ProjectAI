import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import analyze_poem_and_get_suggestions, render_poem_html

st.set_page_config(page_title="מתקן השירים האוטומטי", layout="centered")
st.title("✨ מתקן השירים האוטומטי")
st.write("מודל לניתוח ותיקון שירים.")

if "suggestion_index" not in st.session_state:
    st.session_state.suggestion_index = 0
if "cached_poem" not in st.session_state:
    st.session_state.cached_poem = None
if "cached_data" not in st.session_state:
    st.session_state.cached_data = None

def on_poem_change():
    st.session_state.suggestion_index = 0
    st.session_state.cached_poem = None
    st.session_state.cached_data = None

user_poem = st.text_area(
    "✍️ הדביקי כאן את השיר שלך (רווח של שורה ריקה בין בית לבית):",
    height=200,
    key="current_poem_input",
    on_change=on_poem_change
)

if user_poem:
    # חישוב ההצעות פעם אחת בלבד, שמירה ב-session_state
    if st.session_state.cached_poem != user_poem:
        with st.spinner("🔄 המערכת מנתחת חריזה ומחשבת הצעות..."):
            st.session_state.cached_data = analyze_poem_and_get_suggestions(user_poem)
            st.session_state.cached_poem = user_poem
            st.session_state.suggestion_index = 0

    # רינדור לפי האינדקס הנוכחי - ללא קריאה חוזרת ל-API
    full_poem_html, has_replacements = render_poem_html(
        st.session_state.cached_data,
        st.session_state.suggestion_index
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