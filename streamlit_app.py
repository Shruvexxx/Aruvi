import os
import streamlit as st

# Ensure local modules are importable
from summarizer import summarize_text
from recommender import get_recommendations

# Optional: Google Sheets feedback (uses FEEDBACK_SHEETS_URL secret)
import requests

# ---------- Page / Theme ----------
st.set_page_config(page_title="ARUVI", page_icon="📘", layout="centered")
st.markdown("""
<style>
/* Dark glass background */
.stApp { background: radial-gradient(1200px 700px at 10% -10%, rgba(62,169,255,.12), transparent 60%),
                          radial-gradient(900px 600px at 110% 20%, rgba(127,209,174,.10), transparent 55%),
                          linear-gradient(120deg, #0b0b12, #0f1220); }
.block-container{ padding-top: 2.2rem; }
.aruvi-title { text-align:center; font-size: 2.2rem; color:#9bd3f7; letter-spacing:.08em; }
.card { background: rgba(21,24,41,0.9); border:1px solid rgba(255,255,255,.08); border-radius:16px;
        padding: 1rem 1.1rem; box-shadow: 0 12px 30px rgba(0,0,0,.45); }
.hint { color:#9fb3c8; font-size:0.85rem; }
.link a { color:#9bd3f7; text-decoration:none; }
.link a:hover { text-decoration:underline; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="aruvi-title">ARUVI</div>', unsafe_allow_html=True)

# ---------- Input Card ----------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("**Enter text to summarize**")
    text = st.text_area(" ", placeholder="Paste or type your text here…", height=180, label_visibility="hidden")
    col1, col2 = st.columns([1,1])
    with col1:
        target = st.slider("Target length (words)", min_value=40, max_value=120, value=70, step=5)
    with col2:
        max_sents = st.slider("Max sentences", min_value=2, max_value=6, value=4, step=1)
    go = st.button("Summarize", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

summary = ""
recs = []

if go and text.strip():
    # Summarize (uses your improved TF-IDF + MMR)
    summary = summarize_text(text, target_words=int(target), max_sentences=int(max_sents))
    # Recommend based on the summary (works on your local/included corpus index)
    recs = get_recommendations(summary, top_k=5)

# ---------- Output Card ----------
if summary:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("### Summary")
    st.write(summary)

    if recs:
        st.write("### Recommendations")
        for title, url in recs:
            st.markdown(f"- <span class='link'><a href='{url}' target='_blank'>{title}</a></span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Feedback box (optional Google Sheets)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("### Feedback")
    fb = st.text_area("What was good or missing?", height=110, label_visibility="collapsed")
    if st.button("Submit Feedback", use_container_width=True):
        sheets_url = os.getenv("FEEDBACK_SHEETS_URL", st.secrets.get("FEEDBACK_SHEETS_URL", ""))
        if sheets_url:
            try:
                r = requests.post(sheets_url, json={"summary": summary, "feedback": fb}, timeout=10)
                if r.status_code == 200:
                    st.success("Thanks for the feedback.")
                else:
                    st.warning("Could not submit feedback (non-200).")
            except Exception as e:
                st.warning(f"Feedback error: {e}")
        else:
            st.info("Feedback endpoint not configured. Add FEEDBACK_SHEETS_URL to Streamlit secrets.")
    st.markdown('</div>', unsafe_allow_html=True)
