import streamlit as st
import pandas as pd
import plotly.express as px
from core.interviewer import generate_final_report, ROUND_LABELS


def render_dashboard():
    st.markdown("## 📊 Final Interview Report")

    history = st.session_state.get("history", [])
    if not history:
        st.warning("No answers were recorded.")
        if st.button("Start Over"):
            _reset()
        return

    if "final_report" not in st.session_state:
        with st.spinner("Generating your final review..."):
            st.session_state.final_report = generate_final_report(st.session_state.profile, history)

    report = st.session_state.final_report

    c1, c2, c3 = st.columns(3)
    c1.metric("Overall Score", f"{report['overall_score']}/10")
    c2.metric("Questions Answered", len(history))
    c3.metric("Recommendation", report.get("recommendation", "—"))

    if report.get("round_scores"):
        df = pd.DataFrame(
            [{"Round": ROUND_LABELS.get(r, r), "Avg Score": s} for r, s in report["round_scores"].items()]
        )
        fig = px.bar(df, x="Round", y="Avg Score", range_y=[0, 10], color="Round",
                     title="Average Score by Round", text="Avg Score")
        st.plotly_chart(fig, use_container_width=True)

        # score progression across all questions
        prog_df = pd.DataFrame([
            {"Q#": i + 1, "Score": h.get("score", 0), "Round": ROUND_LABELS.get(h["round"], h["round"])}
            for i, h in enumerate(history)
        ])
        fig2 = px.line(prog_df, x="Q#", y="Score", color="Round", markers=True,
                        range_y=[0, 10], title="Score Progression")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 📝 Summary")
    st.info(report.get("summary", ""))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ✅ Strengths")
        for s in report.get("strengths", []):
            st.markdown(f"- {s}")
    with col2:
        st.markdown("#### ⚠️ Areas to Improve")
        for w in report.get("weaknesses", []):
            st.markdown(f"- {w}")

    st.markdown("#### 🎯 Improvement Plan")
    for tip in report.get("improvement_plan", []):
        st.markdown(f"- {tip}")

    st.divider()
    st.markdown("### 📋 Full Transcript, Scores & Correct Answers")
    for i, h in enumerate(history, 1):
        with st.expander(f"Q{i} [{ROUND_LABELS.get(h['round'], h['round'])}] — Score: {h.get('score','-')}/10"):
            st.markdown(f"**Question:** {h['question']}")
            st.markdown(f"**Your answer:** {h['answer'] or '_(skipped)_'}")
            st.markdown(f"**Verdict:** {h.get('verdict','-')}")
            st.markdown(f"**Feedback:** {h.get('feedback','')}")
            st.markdown(f"**Ideal / correct answer:** {h.get('correct_answer','')}")
            if h.get("strengths"):
                st.markdown("**Strengths:** " + ", ".join(h["strengths"]))
            if h.get("improvements"):
                st.markdown("**Improvements:** " + ", ".join(h["improvements"]))

    st.divider()
    if st.button("🔄 Start a New Interview", use_container_width=True):
        _reset()


def _reset():
    keys_to_clear = [k for k in st.session_state.keys()]
    for k in keys_to_clear:
        del st.session_state[k]
    st.session_state.stage = "setup"
    st.rerun()
