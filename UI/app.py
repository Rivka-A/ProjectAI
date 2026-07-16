# import streamlit as st
# import sys
# import os

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from pipeline import analyze_poem_and_get_suggestions, render_poem_html
# from services.feedback_service import save_feedback, REASON_LABELS
# from services.learning_service import analyze_and_save

# st.set_page_config(page_title="מתקן השירים האוטומטי", layout="centered")
# st.title("✨ מתקן השירים האוטומטי")
# st.write("מודל לניתוח ותיקון שירים.")

# for key, default in [
#     ("suggestion_index", 0),
#     ("cached_poem", None),
#     ("cached_data", None),
#     ("submitted_poem", None),
#     ("replacements_info", []),
#     ("rejected_words", {}),   # {original_word: set(rejected_suggestions)}
# ]:
#     if key not in st.session_state:
#         st.session_state[key] = default


# # --- קלט שיר ---
# user_poem = st.text_area(
#     "✍️ הדביקי כאן את השיר שלך (רווח של שורה ריקה בין בית לבית):",
#     height=200,
#     key="current_poem_input",
# )

# if st.button("📨 שלחי לניתוח"):
#     if user_poem.strip():
#         st.session_state.submitted_poem = user_poem
#         st.session_state.cached_poem = None
#         st.session_state.suggestion_index = 0
#         st.session_state.replacements_info = []
#         st.session_state.rejected_words = {}
#     else:
#         st.warning("נא להזין שיר לפני השליחה.")

# if not st.session_state.submitted_poem:
#     st.stop()

# active_poem = st.session_state.submitted_poem

# # --- חישוב הצעות ---
# if st.session_state.cached_poem != active_poem:
#     rejected_as_sets = {k: set(v) for k, v in st.session_state.rejected_words.items()}
#     with st.spinner("🔄 המערכת מנתחת חריזה ומחשבת הצעות..."):
#         try:
#             st.session_state.cached_data = analyze_poem_and_get_suggestions(
#                 active_poem, rejected_as_sets
#             )
#             st.session_state.cached_poem = active_poem
#             st.session_state.suggestion_index = 0
#         except ConnectionError as e:
#             st.error(f"⚠️ שגיאת תקשורת: {e}")
#             st.stop()

# # --- הצג שיר ---
# full_poem_html, has_replacements, replacements_info, fallback_info = render_poem_html(
#     st.session_state.cached_data,
#     st.session_state.suggestion_index,
#     {k: set(v) for k, v in st.session_state.rejected_words.items()},
# )
# st.session_state.replacements_info = replacements_info

# st.subheader("✨ השיר והסיווגים המעודכנים:")
# st.markdown(full_poem_html, unsafe_allow_html=True)

# if not has_replacements:
#     if fallback_info:
#         st.warning("⚠️ אין עוד הצעות חדשות. להלן הצעות שנפסלו בעבר:")
#         for fb in fallback_info:
#             st.write(f"**שורה {fb['line_num']}:** _{fb['original_line']}_")
#             st.write("הצעות שנפסלו: " + "، ".join(fb['rejected_suggestions']))
#     else:
#         st.write("לא נמצאו שיפורים")
#     st.stop()

# # --- הצג פרטי ההצעות + משוב ---
# if replacements_info:
#     st.write("---")
#     METHOD_LABEL = {
#         'last_word': 'החלפת מילה אחרונה',
#         'extend': 'הוספת מילה',
#         'שינוי סדר מילים': 'שינוי סדר מילים',
#     }
#     reason_options = list(REASON_LABELS.values())

#     # כשיש יותר מחרוז אחד — כל אחד מקבל radio משלו
#     per_rhyme_reasons = {}
#     for i, r in enumerate(replacements_info):
#         method_label = METHOD_LABEL.get(r.get('method', ''), 'שיפור')
#         st.write(f"**📝 הצעת שיפור לשורה {r.get('line2_num', i+1)}:**")
#         col1, col2 = st.columns(2)
#         with col1:
#             st.write("**שורה מקורית:**")
#             st.write(f"_{r.get('original_line', '')}_")
#         with col2:
#             st.write(f"**שורה מוצעת** ({method_label}):")
#             st.write(f"_{r.get('suggested_line', '')}_")

#         if len(replacements_info) > 1:
#             chosen = st.radio(
#                 f"מה דעתך על הצעה זו?",
#                 reason_options,
#                 key=f"feedback_reason_{i}",
#                 label_visibility="visible",
#                 horizontal=True,
#             )
#             per_rhyme_reasons[i] = next(k for k, v in REASON_LABELS.items() if v == chosen)
#             if per_rhyme_reasons[i] == "other":
#                 per_rhyme_reasons[f"{i}_custom"] = st.text_input("פרטי/י:", key=f"feedback_custom_{i}")
#         st.write("")

#     st.write("---")

#     if len(replacements_info) == 1:
#         # משוב רגיל — radio אחד
#         chosen_label = st.radio(
#             "📊 **מה דעתך על ההצעה?**",
#             reason_options,
#             key="feedback_reason_single",
#             label_visibility="visible",
#             horizontal=False,
#         )
#         reason_key = next(k for k, v in REASON_LABELS.items() if v == chosen_label)
#         custom_text = ""
#         if reason_key == "other":
#             custom_text = st.text_input("פרטי/י:", key="feedback_custom_single")

#         if st.button("✅ אשרי ועברי"):
#             for r in st.session_state.replacements_info:
#                 save_feedback(
#                     r["original_word"], r["suggested_word"], reason_key, custom_text,
#                     target_key=r.get("target_key", ""),
#                     suggested_key=r.get("suggested_key", ""),
#                     rhyme_level=r.get("rhyme_level", 0),
#                 )
#             analyze_and_save()
#             if reason_key == "approved":
#                 st.success("מעולה! התיקון נשמר.")
#                 st.session_state.suggestion_index = 0
#             else:
#                 for r in st.session_state.replacements_info:
#                     orig = r["original_word"]
#                     sug  = r["suggested_word"]
#                     if orig not in st.session_state.rejected_words:
#                         st.session_state.rejected_words[orig] = []
#                     if sug not in st.session_state.rejected_words[orig]:
#                         st.session_state.rejected_words[orig].append(sug)
#                 rejected_as_sets = {k: set(v) for k, v in st.session_state.rejected_words.items()}
#                 with st.spinner("🔄 מחשב הצעה חדשה..."):
#                     try:
#                         st.session_state.cached_data = analyze_poem_and_get_suggestions(
#                             active_poem, rejected_as_sets
#                         )
#                         st.session_state.cached_poem = active_poem
#                         st.session_state.suggestion_index += 1
#                     except ConnectionError as e:
#                         st.error(f"⚠️ שגיאת תקשורת: {e}")
#                         st.stop()
#             st.rerun()

#     else:
#         # מספר חרוזים — כפתור "השינוי מבורך לשניים" + כפתור "אשר כל אחד לפי בחירתו"
#         col_all, col_each = st.columns(2)
#         with col_all:
#             if st.button("✅✅ השינוי מבורך לשניים!"):
#                 for r in st.session_state.replacements_info:
#                     save_feedback(
#                         r["original_word"], r["suggested_word"], "approved", "",
#                         target_key=r.get("target_key", ""),
#                         suggested_key=r.get("suggested_key", ""),
#                         rhyme_level=r.get("rhyme_level", 0),
#                     )
#                 analyze_and_save()
#                 st.success("מעולה! שני התיקונים נשמרו.")
#                 st.session_state.suggestion_index = 0
#                 st.rerun()
#         with col_each:
#             if st.button("✅ אשר כל אחד לפי בחירתו"):
#                 any_rejected = False
#                 for i, r in enumerate(st.session_state.replacements_info):
#                     rk = per_rhyme_reasons.get(i, "approved")
#                     ct = per_rhyme_reasons.get(f"{i}_custom", "")
#                     save_feedback(
#                         r["original_word"], r["suggested_word"], rk, ct,
#                         target_key=r.get("target_key", ""),
#                         suggested_key=r.get("suggested_key", ""),
#                         rhyme_level=r.get("rhyme_level", 0),
#                     )
#                     if rk != "approved":
#                         any_rejected = True
#                         orig = r["original_word"]
#                         sug  = r["suggested_word"]
#                         if orig not in st.session_state.rejected_words:
#                             st.session_state.rejected_words[orig] = []
#                         if sug not in st.session_state.rejected_words[orig]:
#                             st.session_state.rejected_words[orig].append(sug)
#                 analyze_and_save()
#                 if any_rejected:
#                     rejected_as_sets = {k: set(v) for k, v in st.session_state.rejected_words.items()}
#                     with st.spinner("🔄 מחשב הצעות חדשות..."):
#                         try:
#                             st.session_state.cached_data = analyze_poem_and_get_suggestions(
#                                 active_poem, rejected_as_sets
#                             )
#                             st.session_state.cached_poem = active_poem
#                             st.session_state.suggestion_index += 1
#                         except ConnectionError as e:
#                             st.error(f"⚠️ שגיאת תקשורת: {e}")
#                             st.stop()
#                 st.rerun()
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
        try:
            st.session_state.cached_data = analyze_poem_and_get_suggestions(
                active_poem, rejected_as_sets
            )
            st.session_state.cached_poem = active_poem
            st.session_state.suggestion_index = 0
        except ConnectionError as e:
            st.error(f"⚠️ שגיאת תקשורת: {e}")
            st.stop()

# --- הצג שיר ---
full_poem_html, has_replacements, replacements_info, fallback_info = render_poem_html(
    st.session_state.cached_data,
    st.session_state.suggestion_index,
    {k: set(v) for k, v in st.session_state.rejected_words.items()},
)
st.session_state.replacements_info = replacements_info

st.subheader("✨ השיר והסיווגים המעודכנים:")
st.markdown(full_poem_html, unsafe_allow_html=True)

if not has_replacements:
    if fallback_info:
        st.warning("⚠️ אין עוד הצעות חדשות. להלן הצעות שנפסלו בעבר:")
        for fb in fallback_info:
            st.write(f"**שורה {fb['line_num']}:** _{fb['original_line']}_")
            if fb.get('message'):
                st.caption(fb['message'])
            st.write("הצעות שנפסלו: " + "، ".join(fb['rejected_suggestions']))
    else:
        st.write("לא נמצאו שיפורים")
    st.stop()

# --- הצג פרטי ההצעות + משוב ---
if replacements_info:
    st.write("---")
    METHOD_LABEL = {
        'last_word': 'החלפת מילה אחרונה',
        'extend': 'הוספת מילה',
        'שינוי סדר מילים': 'שינוי סדר מילים',
    }
    reason_options = list(REASON_LABELS.values())

    # כשיש יותר מחרוז אחד — כל אחד מקבל radio משלו
    per_rhyme_reasons = {}
    for i, r in enumerate(replacements_info):
        method_label = METHOD_LABEL.get(r.get('method', ''), 'שיפור')
        st.write(f"**📝 הצעת שיפור לשורה {r.get('line2_num', i+1)}:**")
        if r.get('soft_warning_fallback'):
            st.warning("⚠️ זו הצעה שכבר סומנה כ'לא אהבתי' בעבר — מוצגת כי לא נמצאה חלופה אחרת.")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**שורה מקורית:**")
            st.write(f"_{r.get('original_line', '')}_")
        with col2:
            st.write(f"**שורה מוצעת** ({method_label}):")
            st.write(f"_{r.get('suggested_line', '')}_")

        if len(replacements_info) > 1:
            chosen = st.radio(
                f"מה דעתך על הצעה זו?",
                reason_options,
                key=f"feedback_reason_{i}",
                label_visibility="visible",
                horizontal=True,
            )
            per_rhyme_reasons[i] = next(k for k, v in REASON_LABELS.items() if v == chosen)
            if per_rhyme_reasons[i] == "other":
                per_rhyme_reasons[f"{i}_custom"] = st.text_input("פרטי/י:", key=f"feedback_custom_{i}")
        st.write("")

    st.write("---")

    if len(replacements_info) == 1:
        # משוב רגיל — radio אחד
        chosen_label = st.radio(
            "📊 **מה דעתך על ההצעה?**",
            reason_options,
            key="feedback_reason_single",
            label_visibility="visible",
            horizontal=False,
        )
        reason_key = next(k for k, v in REASON_LABELS.items() if v == chosen_label)
        custom_text = ""
        if reason_key == "other":
            custom_text = st.text_input("פרטי/י:", key="feedback_custom_single")

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
                for r in st.session_state.replacements_info:
                    orig = r["original_word"]
                    sug  = r["suggested_word"]
                    if orig not in st.session_state.rejected_words:
                        st.session_state.rejected_words[orig] = []
                    if sug not in st.session_state.rejected_words[orig]:
                        st.session_state.rejected_words[orig].append(sug)
                rejected_as_sets = {k: set(v) for k, v in st.session_state.rejected_words.items()}
                with st.spinner("🔄 מחשב הצעה חדשה..."):
                    try:
                        st.session_state.cached_data = analyze_poem_and_get_suggestions(
                            active_poem, rejected_as_sets
                        )
                        st.session_state.cached_poem = active_poem
                        st.session_state.suggestion_index += 1
                    except ConnectionError as e:
                        st.error(f"⚠️ שגיאת תקשורת: {e}")
                        st.stop()
            st.rerun()

    else:
        # מספר חרוזים — כפתור "השינוי מבורך לשניים" + כפתור "אשר כל אחד לפי בחירתו"
        col_all, col_each = st.columns(2)
        with col_all:
            if st.button("✅✅ השינוי מבורך לשניים!"):
                for r in st.session_state.replacements_info:
                    save_feedback(
                        r["original_word"], r["suggested_word"], "approved", "",
                        target_key=r.get("target_key", ""),
                        suggested_key=r.get("suggested_key", ""),
                        rhyme_level=r.get("rhyme_level", 0),
                    )
                analyze_and_save()
                st.success("מעולה! שני התיקונים נשמרו.")
                st.session_state.suggestion_index = 0
                st.rerun()
        with col_each:
            if st.button("✅ אשר כל אחד לפי בחירתו"):
                any_rejected = False
                for i, r in enumerate(st.session_state.replacements_info):
                    rk = per_rhyme_reasons.get(i, "approved")
                    ct = per_rhyme_reasons.get(f"{i}_custom", "")
                    save_feedback(
                        r["original_word"], r["suggested_word"], rk, ct,
                        target_key=r.get("target_key", ""),
                        suggested_key=r.get("suggested_key", ""),
                        rhyme_level=r.get("rhyme_level", 0),
                    )
                    if rk != "approved":
                        any_rejected = True
                        orig = r["original_word"]
                        sug  = r["suggested_word"]
                        if orig not in st.session_state.rejected_words:
                            st.session_state.rejected_words[orig] = []
                        if sug not in st.session_state.rejected_words[orig]:
                            st.session_state.rejected_words[orig].append(sug)
                analyze_and_save()
                if any_rejected:
                    rejected_as_sets = {k: set(v) for k, v in st.session_state.rejected_words.items()}
                    with st.spinner("🔄 מחשב הצעות חדשות..."):
                        try:
                            st.session_state.cached_data = analyze_poem_and_get_suggestions(
                                active_poem, rejected_as_sets
                            )
                            st.session_state.cached_poem = active_poem
                            st.session_state.suggestion_index += 1
                        except ConnectionError as e:
                            st.error(f"⚠️ שגיאת תקשורת: {e}")
                            st.stop()
                st.rerun()