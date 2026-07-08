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
    ("rejected_words", {}),   # {original_word: set(rejected_suggestions)}
]:
    if key not in st.session_state:
        st.session_state[key] = default


# --- קלט שיר ---
user_poem = st.text_area(
    "✍️ הדביקי כאן את השיר שלך (רווח של שורה ריקה בין בית לבית):",
    height=200,
    key="current_poem_input",
)

if st.button("📨 שלחי לניתוח"):
    if user_poem.strip():
        st.session_state.submitted_poem = user_poem
        st.session_state.cached_poem = None
        st.session_state.suggestion_index = 0
        st.session_state.replacements_info = []
        st.session_state.rejected_words = {}
    else:
        st.warning("נא להזין שיר לפני השליחה.")

if not st.session_state.submitted_poem:
    st.stop()

active_poem = st.session_state.submitted_poem

# --- חישוב הצעות ---
if st.session_state.cached_poem != active_poem:
    rejected_as_sets = {k: set(v) for k, v in st.session_state.rejected_words.items()}
    with st.spinner("🔄 המערכת מנתחת חריזה ומחשבת הצעות..."):
        st.session_state.cached_data = analyze_poem_and_get_suggestions(
            active_poem, rejected_as_sets
        )
        st.session_state.cached_poem = active_poem
        st.session_state.suggestion_index = 0

# --- הצג שיר ---
full_poem_html, has_replacements, replacements_info = render_poem_html(
    st.session_state.cached_data,
    st.session_state.suggestion_index,
    {k: set(v) for k, v in st.session_state.rejected_words.items()},
)
st.session_state.replacements_info = replacements_info

st.subheader("✨ השיר והסיווגים המעודכנים:")
st.markdown(full_poem_html, unsafe_allow_html=True)

if not has_replacements:
    st.write("לא נמצאו שיפורים")
    st.stop()

# --- הצג פרטי ההצעה הנוכחית ---
if replacements_info:
    st.write("---")
    st.write("**📝 הצעת שיפור:**")
    for r in replacements_info:
        method_label = {
            'last_word': 'החלפת מילה אחרונה',
            'extend': 'הוספת מילה',
        }.get(r.get('method', ''), 'שיפור')

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**שורה מקורית:**")
            st.write(f"_{r.get('original_line', '')}_")
        with col2:
            st.write(f"**שורה מוצעת** ({method_label}):")
            st.write(f"_{r.get('suggested_line', '')}_")

# --- כפתור תיקון (רינדור רק אחרי לחיצה) ---
st.write("---")
st.write(f"📊 **מה דעתך על ההצעה? **")

reason_options = list(REASON_LABELS.values())
chosen_label = st.radio(
    "בחרי:",
    reason_options,
    key="feedback_reason",
    label_visibility="collapsed",
    horizontal=False,
)
reason_key = next(k for k, v in REASON_LABELS.items() if v == chosen_label)

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
    analyze_and_save()

    if reason_key == "approved":
        st.success("מעולה! התיקון נשמר.")
        st.session_state.suggestion_index = 0
    else:
        # שמור את המילה הנדחית
        for r in st.session_state.replacements_info:
            orig = r["original_word"]
            sug  = r["suggested_word"]
            if orig not in st.session_state.rejected_words:
                st.session_state.rejected_words[orig] = []
            if sug not in st.session_state.rejected_words[orig]:
                st.session_state.rejected_words[orig].append(sug)

        # חשב מחדש עם המילים הנדחיות
        rejected_as_sets = {k: set(v) for k, v in st.session_state.rejected_words.items()}
        with st.spinner("🔄 מחשב הצעה חדשה..."):
            st.session_state.cached_data = analyze_poem_and_get_suggestions(
                active_poem, rejected_as_sets
            )
            st.session_state.cached_poem = active_poem
            # אל תאפס את suggestion_index — המשך לחלופה הבאה
            st.session_state.suggestion_index += 1
    st.rerun()
    