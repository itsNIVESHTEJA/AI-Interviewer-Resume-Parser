import streamlit as st
from core.resume_parser import extract_text_from_pdf, parse_resume_and_jd


def render_setup_panel():
    st.markdown("## 🎤 AI Live Interviewer")
    st.caption("Upload your resume and a job description to start a realistic, voice-enabled mock interview.")

    with st.form("setup_form"):
        col1, col2 = st.columns(2)
        with col1:
            resume_file = st.file_uploader("📄 Resume (PDF)", type=["pdf"])
        with col2:
            jd_text = st.text_area("🧾 Job Description (paste text)", height=180,
                                    placeholder="Paste the job description here (optional but recommended)...")

        colr1, colr2, colr3 = st.columns(3)
        with colr1:
            unlimited = st.checkbox("Unlimited questions per round", value=True)
        with colr2:
            q_per_round = st.number_input("If not unlimited: questions/round", min_value=2, max_value=20, value=5)
        with colr3:
            voice_mode = st.checkbox("🔊 Enable voice (TTS + mic)", value=True)

        submitted = st.form_submit_button("🚀 Parse & Start Interview", use_container_width=True)

    if submitted:
        if not resume_file:
            st.error("Please upload your resume (PDF) to continue.")
            return

        with st.spinner("Parsing resume and matching against job description..."):
            resume_bytes = resume_file.read()
            resume_text = extract_text_from_pdf(resume_bytes)
            if not resume_text.strip():
                st.error("Couldn't extract text from that PDF. Try another file (must contain selectable text, not a scanned image).")
                return
            profile = parse_resume_and_jd(resume_text, jd_text or "")

        st.session_state.profile = profile
        st.session_state.resume_text = resume_text
        st.session_state.jd_text = jd_text
        st.session_state.unlimited = unlimited
        st.session_state.q_per_round = q_per_round
        st.session_state.voice_mode = voice_mode
        st.session_state.stage = "confirm"
        st.rerun()
