"""
Core interview engine.

Rounds (in order), each unlimited length until the user/interviewer ends it:
  1. INTRO       - "Tell me about yourself" + light follow-ups
  2. TECHNICAL   - questions on resume skills / JD required skills (concepts)
  3. CODING      - coding / problem-solving questions on top skills
  4. HR          - behavioral / HR questions

For every candidate answer we ask the LLM to verify/score it and produce
feedback + a model/correct answer. At the end we build a full review.
"""
import random
from core.groq_client import chat, chat_json

ROUNDS = ["intro", "technical", "coding", "hr"]

ROUND_LABELS = {
    "intro": "Introduction",
    "technical": "Technical (Skills)",
    "coding": "Coding / Problem Solving",
    "hr": "HR / Behavioral",
}


def _profile_context(profile: dict) -> str:
    return f"""
Candidate name: {profile.get('name')}
Target role: {profile.get('jd_role')}
Resume summary: {profile.get('resume_summary')}
Skills: {', '.join(profile.get('skills', [])) or 'N/A'}
JD required skills: {', '.join(profile.get('jd_required_skills', [])) or 'N/A'}
Matched skills: {', '.join(profile.get('matched_skills', [])) or 'N/A'}
Missing skills: {', '.join(profile.get('missing_skills', [])) or 'N/A'}
Projects: {"; ".join(p.get('name','') + ' - ' + p.get('description','') for p in profile.get('projects', [])) or 'N/A'}
Experience: {"; ".join(profile.get('experience', [])) or 'N/A'}
"""


def generate_next_question(profile: dict, round_name: str, history: list, asked_count: int) -> str:
    """
    history: list of {"round":..., "question":..., "answer":..., "score":...}
    asked_count: number of questions already asked in THIS round.
    """
    if round_name == "intro" and asked_count == 0:
        return "Tell me about yourself."

    recent_history = history[-6:]
    hist_text = "\n".join(
        f"[{h['round']}] Q: {h['question']}\nA: {h['answer']}\nScore: {h.get('score','-')}/10"
        for h in recent_history
    ) or "No questions asked yet in this interview."

    round_instructions = {
        "intro": (
            "Ask a natural, brief follow-up question about the candidate's background, "
            "motivation, or career goals based on their previous answer. Keep it conversational."
        ),
        "technical": (
            "Ask ONE technical/conceptual interview question testing the candidate's depth "
            "on their listed skills or the job's required skills (e.g. 'Explain how X works', "
            "'What is the difference between X and Y', 'How would you design/debug X'). "
            "Increase difficulty gradually. Do not repeat earlier questions."
        ),
        "coding": (
            "Ask ONE coding / problem-solving interview question relevant to the candidate's "
            "strongest programming skills or the JD (e.g. algorithm, data structure, "
            "write pseudocode/code for X, complexity analysis, debugging a snippet). "
            "State it clearly as a problem statement. Do not repeat earlier questions."
        ),
        "hr": (
            "Ask ONE HR / behavioral interview question (teamwork, conflict, leadership, "
            "failure, strengths/weaknesses, why this company/role, salary/relocation, etc). "
            "Do not repeat earlier questions."
        ),
    }

    system = (
        "You are a professional, friendly but rigorous AI interviewer conducting a live "
        f"{ROUND_LABELS[round_name]} round for the role of {profile.get('jd_role')}. "
        "Ask exactly one question at a time, natural spoken interview tone, no numbering, "
        "no preamble like 'Sure, here's a question' — just ask it directly."
    )
    user = f"""
Candidate profile:
{_profile_context(profile)}

Conversation so far (most recent):
{hist_text}

{round_instructions[round_name]}

Return ONLY the question text, nothing else.
"""
    question = chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.8,
        max_tokens=200,
    ).strip().strip('"')
    return question


def evaluate_answer(profile: dict, round_name: str, question: str, answer: str) -> dict:
    """
    Returns:
    {
      "score": int 0-10,
      "verdict": "correct/partially correct/incorrect" (loosely),
      "feedback": str,
      "correct_answer": str,   # model/ideal answer or key points
      "strengths": [str],
      "improvements": [str]
    }
    """
    system = (
        "You are a strict but fair technical interview evaluator. "
        "Evaluate the candidate's spoken answer to an interview question. "
        "Respond with STRICT JSON only, matching the given schema."
    )
    user = f"""
Role: {profile.get('jd_role')}
Round: {ROUND_LABELS[round_name]}
Question: {question}
Candidate's answer: {answer if answer.strip() else "(No answer provided / skipped)"}

Return JSON:
{{
  "score": integer 0-10 (0 if no answer/irrelevant),
  "verdict": "correct" | "partially correct" | "incorrect",
  "feedback": "2-3 sentence constructive feedback spoken directly to the candidate",
  "correct_answer": "concise ideal/model answer or key points the candidate should have covered",
  "strengths": ["short phrases, may be empty"],
  "improvements": ["short phrases, may be empty"]
}}
"""
    data = chat_json(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
        max_tokens=700,
    )
    data.setdefault("score", 0)
    data.setdefault("verdict", "incorrect")
    data.setdefault("feedback", "")
    data.setdefault("correct_answer", "")
    data.setdefault("strengths", [])
    data.setdefault("improvements", [])
    try:
        data["score"] = max(0, min(10, int(data["score"])))
    except (ValueError, TypeError):
        data["score"] = 0
    return data


def generate_final_report(profile: dict, history: list) -> dict:
    """
    Builds an overall interview report using all Q&A history.
    Returns:
    {
      "overall_score": float (0-10),
      "round_scores": {round: avg_score},
      "summary": str,
      "strengths": [str],
      "weaknesses": [str],
      "recommendation": "Strong Hire"|"Hire"|"Borderline"|"No Hire",
      "improvement_plan": [str]
    }
    """
    if not history:
        return {
            "overall_score": 0,
            "round_scores": {},
            "summary": "No questions were answered.",
            "strengths": [],
            "weaknesses": [],
            "recommendation": "No Hire",
            "improvement_plan": [],
        }

    round_scores = {}
    for r in ROUNDS:
        scores = [h["score"] for h in history if h["round"] == r and "score" in h]
        if scores:
            round_scores[r] = round(sum(scores) / len(scores), 2)

    overall = round(sum(h["score"] for h in history if "score" in h) / max(1, len([h for h in history if "score" in h])), 2)

    hist_text = "\n".join(
        f"[{ROUND_LABELS.get(h['round'], h['round'])}] Q: {h['question']}\nA: {h['answer']}\nScore: {h.get('score','-')}/10\nFeedback: {h.get('feedback','')}"
        for h in history
    )

    system = (
        "You are a senior hiring panel lead summarizing a full interview into a final "
        "report for the candidate. Respond with STRICT JSON only."
    )
    user = f"""
Candidate profile:
{_profile_context(profile)}

Full interview transcript with scores/feedback:
{hist_text}

Return JSON:
{{
  "summary": "4-6 sentence overall performance summary",
  "strengths": ["3-6 concrete strengths observed"],
  "weaknesses": ["3-6 concrete weaknesses / gaps observed"],
  "recommendation": "Strong Hire" | "Hire" | "Borderline" | "No Hire",
  "improvement_plan": ["3-5 concrete actionable tips to improve"]
}}
"""
    data = chat_json(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.4,
        max_tokens=900,
    )
    data.setdefault("summary", "")
    data.setdefault("strengths", [])
    data.setdefault("weaknesses", [])
    data.setdefault("recommendation", "Borderline")
    data.setdefault("improvement_plan", [])
    data["overall_score"] = overall
    data["round_scores"] = round_scores
    return data
