import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import analyze_poem_and_get_suggestions, render_poem_html
from services.feedback_service import save_feedback, REASON_LABELS
from services.learning_service import analyze_and_save

st.set_page_config(page_title="מתקן השירים האוטומטי", layout="centered")
st.title("✨ מתקן השירים האוטומטי")
st.write("מודל לניתוח ותיקון שירים.")

for key, default in [
    ("suggestion_index", 0),
    ("cached_poem", None),
    ("cached_data", None),
    ("submitted_poem", None),
    ("replacements_info", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# --- קלט שיר עם כפתור שליחה ---
user_poem = st.text_area(
    "✍️ הדביקי כאן את השיר שלך (רווח של שורה ריקה בין בית לבית):",
    height=200,
    key="current_poem_input",
)

if st.button("📨 שלחי לניתוח"):
    if user_poem.strip():
        st.session_state.submitted_poem = user_poem
        st.session_state.cached_poem = None   # כפה חישוב מחדש
        st.session_state.suggestion_index = 0
        st.session_state.replacements_info = []
    else:
        st.warning("נא להזין שיר לפני השליחה.")

if not st.session_state.submitted_poem:
    st.stop()

active_poem = st.session_state.submitted_poem

# --- חישוב הצעות פעם אחת בלבד ---
if st.session_state.cached_poem != active_poem:
    with st.spinner("🔄 המערכת מנתחת חריזה ומחשבת הצעות..."):
        st.session_state.cached_data = analyze_poem_and_get_suggestions(active_poem)
        st.session_state.cached_poem = active_poem
        st.session_state.suggestion_index = 0

full_poem_html, has_replacements, replacements_info = render_poem_html(
    st.session_state.cached_data,
    st.session_state.suggestion_index,
)
st.session_state.replacements_info = replacements_info

st.subheader("✨ השיר והסיווגים המעודכנים:")
st.markdown(full_poem_html, unsafe_allow_html=True)

if not has_replacements:
    st.stop()

# --- פאנל משוב: הרשימה מחליפה את הכפתורים ---
st.write("---")
current_num = st.session_state.suggestion_index + 1
st.write(f"📊 **מה דעתך על ההצעה? (מציג כעת חלופה מספר {current_num})**")

reason_options = list(REASON_LABELS.values())
chosen_label = st.radio(
    "בחרי:",
    reason_options,
    key="feedback_reason",
    label_visibility="collapsed",
    horizontal=False,
)
reason_key = next(k for k, v in REASON_LABELS.items() if v == chosen_label)

# שדה "אחר" מופיע מיידית בלי לחיצת כפתור
custom_text = ""
if reason_key == "other":
    custom_text = st.text_input("פרטי/י:", key="feedback_custom")

if st.button("✅ אשרי ועברי"):
    for r in st.session_state.replacements_info:
        save_feedback(
            r["original_word"], r["suggested_word"], reason_key, custom_text,
            target_key=r.get("target_key", ""),
            suggested_key=r.get("suggested_key", ""),
            rhyme_level=r.get("rhyme_level", 0),
        )
    analyze_and_save()  # עדכון כללי הלמידה

    if reason_key == "approved":
        st.success("מעולה! התיקון נשמר.")
        st.session_state.suggestion_index = 0
    else:
        st.session_state.suggestion_index += 1
        if reason_key in ("worse_rhyme", "bad_context", "dislike", "other"):
            with st.spinner("🔄 מחשב הצעה חדשה..."):
                st.session_state.cached_data = analyze_poem_and_get_suggestions(active_poem)
                st.session_state.suggestion_index = 0

    st.rerun()
