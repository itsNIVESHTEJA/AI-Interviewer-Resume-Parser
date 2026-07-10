import streamlit as st
from core.interviewer import ROUNDS, ROUND_LABELS, generate_next_question, evaluate_answer
from voice.tts import synthesize_speech


def render_confirm_panel():
    profile = st.session_state.profile
    st.markdown("## ✅ Parsed Profile")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Candidate:** {profile.get('name')}")
        st.markdown(f"**Target Role:** {profile.get('jd_role')}")
        st.markdown("**Skills:** " + ", ".join(profile.get("skills", [])[:20]))
        st.markdown("**Matched with JD:** " + (", ".join(profile.get("matched_skills", [])) or "—"))
        st.markdown("**Missing vs JD:** " + (", ".join(profile.get("missing_skills", [])) or "—"))
    with c2:
        st.markdown("**Summary:**")
        st.info(profile.get("resume_summary", ""))
        if profile.get("projects"):
            st.markdown("**Projects:**")
            for p in profile["projects"][:5]:
                st.markdown(f"- **{p.get('name','')}**: {p.get('description','')}")

    st.divider()
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🎙️ Start Interview", use_container_width=True, type="primary"):
            st.session_state.stage = "interview"
            st.session_state.round_idx = 0
            st.session_state.history = []
            st.session_state.round_counts = {r: 0 for r in ROUNDS}
            st.session_state.current_question = None
            st.session_state.awaiting_eval = False
            st.rerun()
    with colB:
        if st.button("⬅️ Re-upload", use_container_width=True):
            st.session_state.stage = "setup"
            st.rerun()


def _speak(text: str):
    if st.session_state.get("voice_mode"):
        try:
            audio = synthesize_speech(text)
            if audio:
                st.audio(audio, format="audio/mp3", autoplay=True)
        except Exception as e:
            st.caption(f"(voice unavailable: {e})")


def _current_round():
    return ROUNDS[st.session_state.round_idx]


def _ensure_question():
    """Generate the current question if we don't have one yet."""
    if st.session_state.current_question is None:
        round_name = _current_round()
        count = st.session_state.round_counts[round_name]
        with st.spinner("Interviewer is thinking of a question..."):
            q = generate_next_question(
                st.session_state.profile, round_name, st.session_state.history, count
            )
        st.session_state.current_question = q
        st.session_state.last_eval = None


def render_chat_view():
    profile = st.session_state.profile
    round_name = _current_round()

    # Sidebar-ish progress
    st.markdown(f"### Round {st.session_state.round_idx + 1}/4 — {ROUND_LABELS[round_name]}")
    prog = (st.session_state.round_idx) / len(ROUNDS)
    st.progress(prog)

    _ensure_question()
    question = st.session_state.current_question

    # --- Chat history (left interviewer / right candidate) ---
    for h in st.session_state.history[-10:]:
        with st.chat_message("assistant"):
            st.markdown(f"**[{ROUND_LABELS[h['round']]}]** {h['question']}")
        with st.chat_message("user"):
            st.markdown(h["answer"] or "_(no answer)_")
            if "score" in h:
                st.caption(f"Score: {h['score']}/10 — {h.get('verdict','')}")
                with st.expander("Feedback & correct answer"):
                    st.write(h.get("feedback", ""))
                    st.markdown(f"**Ideal answer:** {h.get('correct_answer','')}")

    # --- Current question ---
    with st.chat_message("assistant"):
        st.markdown(f"**[{ROUND_LABELS[round_name]}]** {question}")
        if st.session_state.get("voice_mode") and not st.session_state.get(f"spoken_{question}"):
            _speak(question)
            st.session_state[f"spoken_{question}"] = True

    # --- Answer input: text + optional mic ---
    answer_text = st.session_state.get("draft_answer", "")

    if st.session_state.get("voice_mode"):
        try:
            from audio_recorder_streamlit import audio_recorder
            st.caption("🎙️ Record your spoken answer, or type below.")
            audio_bytes = audio_recorder(text="", icon_size="2x", key=f"rec_{len(st.session_state.history)}")
            if audio_bytes:
                from voice.stt import transcribe_audio
                with st.spinner("Transcribing..."):
                    try:
                        transcribed = transcribe_audio(audio_bytes)
                        if transcribed:
                            answer_text = transcribed
                            st.success(f"Transcribed: {transcribed}")
                        else:
                            st.warning("Couldn't understand the audio, please try again or type your answer.")
                    except Exception as e:
                        st.warning(f"Voice transcription failed ({e}). Please type your answer instead.")
        except ImportError:
            st.caption("(Install `audio-recorder-streamlit` to enable mic recording.)")

    with st.form(key=f"answer_form_{len(st.session_state.history)}", clear_on_submit=True):
        typed = st.text_area("Your answer", value=answer_text, height=120,
                              placeholder="Type or use the mic above, then submit...")
        col1, col2, col3 = st.columns([1, 1, 1])
        submit = col1.form_submit_button("✅ Submit Answer", use_container_width=True)
        skip = col2.form_submit_button("⏭️ Skip Question", use_container_width=True)
        end_round = col3.form_submit_button("⏹️ End This Round", use_container_width=True)

    if submit or skip:
        final_answer = "" if skip else typed
        with st.spinner("Evaluating your answer..."):
            eval_result = evaluate_answer(profile, round_name, question, final_answer)
        st.session_state.history.append({
            "round": round_name,
            "question": question,
            "answer": final_answer,
            **eval_result,
        })
        st.session_state.round_counts[round_name] += 1
        st.session_state.current_question = None
        st.rerun()

    if end_round:
        _advance_round()
        st.rerun()

    st.divider()
    colx, coly = st.columns(2)
    with colx:
        if st.button("➡️ Next Round", use_container_width=True):
            _advance_round()
            st.rerun()
    with coly:
        if st.button("🏁 End Interview & See Report", use_container_width=True, type="primary"):
            st.session_state.stage = "report"
            st.rerun()


def _advance_round():
    if st.session_state.round_idx < len(ROUNDS) - 1:
        st.session_state.round_idx += 1
        st.session_state.current_question = None
    else:
        st.session_state.stage = "report"
