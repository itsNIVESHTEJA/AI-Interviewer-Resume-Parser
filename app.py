import os
import streamlit as st
from dotenv import load_dotenv

from ui.setup_panel import render_setup_panel
from ui.chat_view import render_confirm_panel, render_chat_view
from ui.dashboard import render_dashboard

load_dotenv()

st.set_page_config(page_title="AI Live Interviewer", page_icon="🎤", layout="wide")

# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "stage" not in st.session_state:
    st.session_state.stage = "setup"

if not os.getenv("GROQ_API_KEY"):
    st.warning(
        "⚠️ GROQ_API_KEY not found. Create a `.env` file in the project root "
        "(see `.env.example`) with `GROQ_API_KEY=your_key_here` and restart the app.",
        icon="⚠️",
    )

stage = st.session_state.stage

if stage == "setup":
    render_setup_panel()
elif stage == "confirm":
    render_confirm_panel()
elif stage == "interview":
    render_chat_view()
elif stage == "report":
    render_dashboard()
else:
    st.session_state.stage = "setup"
    st.rerun()
