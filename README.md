#  AI Live Interviewer 

A Streamlit app that runs a full mock interview from your resume + a job description:
parses skills/projects, asks unlimited questions across **Intro → Technical → Coding → HR**
rounds, verifies each answer with scoring + the ideal answer, and ends with a full
report + charts. Voice-enabled (TTS asks questions out loud, mic lets you answer by speaking).

## Project Structure
```
ai_interviewer/
├── app.py                    # Main Streamlit entrypoint / stage router
├── .env.example               # Copy to .env and add your GROQ_API_KEY
├── requirements.txt
├── core/
│   ├── groq_client.py         # Groq LLM wrapper (chat + JSON mode)
│   ├── resume_parser.py       # PDF → text, then LLM → structured profile vs JD
│   └── interviewer.py         # Round logic, question gen, answer eval, final report
├── voice/
│   ├── tts.py                 # Text-to-speech (gTTS -> mp3 bytes)
│   └── stt.py                 # Speech-to-text (SpeechRecognition, mic wav -> text)
├── ui/
│   ├── setup_panel.py         # Resume upload + JD paste
│   ├── chat_view.py           # Confirm profile + live interview chat
│   ├── input_bar.py           # (structure placeholder, see chat_view.py)
│   └── dashboard.py           # Final scores, charts, transcript, recommendation
└── assets/style.css
```

## Setup (5 minutes)

```bash
cd ai_interviewer
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create `.env` in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free key at https://console.groq.com/keys

Run:
```bash
streamlit run app.py
```

## How it works / demo flow

1. **Setup** – upload your resume PDF, paste the JD (optional), choose unlimited
   questions or a fixed number per round, toggle voice on/off.
2. **Parsing** – `resume_parser.py` extracts PDF text with `pypdf`, then sends
   resume + JD text to Groq's LLM with a strict JSON schema to extract name,
   skills, projects, experience, education, and to compute matched/missing
   skills vs the JD.
3. **Confirm** – review the parsed profile before starting.
4. **Interview** – `interviewer.py` drives 4 rounds:
   - **Intro**: "Tell me about yourself" + natural follow-ups.
   - **Technical**: conceptual questions on your skills / JD requirements.
   - **Coding**: problem-solving / algorithm / debugging questions.
   - **HR**: behavioral questions.
   Each round is unlimited — keep answering, or hit "Next Round" / "End Round" any time.
   Every question can be **spoken aloud (TTS)** and you can **answer by voice (STT)**
   or by typing. Every answer is scored 0–10 with feedback + the ideal answer shown
   immediately (in an expander so it doesn't spoil the live flow).
5. **Report** – `dashboard.py` calls `generate_final_report()` for an overall
   score, per-round average score chart, score progression line chart,
   strengths/weaknesses, a hire recommendation, an improvement plan, and the
   full transcript with every correct answer.

## Notes for your explanation

- **LLM**: Groq API (`llama-3.3-70b-versatile` by default, configurable via
  `GROQ_MODEL` env var) — used for parsing, question generation, answer
  evaluation, and the final report. All calls are centralized in
  `core/groq_client.py` with a `chat_json()` helper that enforces structured
  JSON output for reliable parsing.
- **Resume parsing**: `pypdf` extracts raw text; the LLM structures it (skills,
  projects, experience, education) and cross-references it against the JD to
  compute matched/missing skills — this is what earlier drove "resume parsing +
  skills/projects extraction" in your original app.
- **Voice**: `gTTS` converts each question to speech (played via
  `st.audio(autoplay=True)`); `audio-recorder-streamlit` captures the mic in
  the browser and `SpeechRecognition` (Google Web Speech API) transcribes it —
  same idea as the original `voice/tts.py` / `voice/stt.py` but hardened
  (gTTS instead of pyttsx3, which often has no system voice on servers/cloud).
- **Unlimited rounds**: each round loops in Streamlit session state
  (`round_counts`) with no upper bound unless you turn off "Unlimited
  questions per round" at setup — you decide when to move on or end.
- **Scoring**: `evaluate_answer()` asks the LLM for a 0–10 score, verdict,
  feedback, the ideal/correct answer, and strengths/improvements — all shown
  per question and aggregated into the final dashboard.

## Troubleshooting

- `GROQ_API_KEY not set` — make sure `.env` is in the project root (same
  folder as `app.py`) and you restarted `streamlit run app.py` after adding it.
- Mic not showing up — `audio-recorder-streamlit` needs browser mic
  permission; if it's not installed/working, just type your answer instead.
- PDF text extraction empty — the PDF is likely a scanned image; export your
  resume as a text-based PDF (e.g. from Word/Google Docs) instead.
