"""
Extracts raw text from an uploaded resume (PDF) and uses the LLM to turn
resume text + job description text into a structured profile:
skills, projects, experience, education — plus a skill/JD match summary.
"""
from io import BytesIO
from pypdf import PdfReader
from core.groq_client import chat_json


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()


def parse_resume_and_jd(resume_text: str, jd_text: str) -> dict:
    """
    Returns a structured dict:
    {
      "name": str,
      "skills": [str],
      "projects": [{"name": str, "description": str, "tech": [str]}],
      "experience": [str],
      "education": [str],
      "jd_role": str,
      "jd_required_skills": [str],
      "matched_skills": [str],
      "missing_skills": [str],
      "resume_summary": str
    }
    """
    system = (
        "You are an expert technical recruiter and resume parser. "
        "Extract structured information from a resume and compare it "
        "against a job description. Always respond with STRICT JSON only, "
        "matching exactly the schema given by the user, no markdown, no commentary."
    )
    user = f"""
Resume text:
---
{resume_text[:8000]}
---

Job description text:
---
{jd_text[:4000] if jd_text.strip() else "No JD provided. Infer a likely role from the resume."}
---

Return JSON with this exact schema:
{{
  "name": "candidate name or 'Candidate' if unknown",
  "skills": ["list of technical skills found in resume"],
  "projects": [{{"name": "...", "description": "...", "tech": ["..."]}}],
  "experience": ["short bullet strings describing work experience"],
  "education": ["short bullet strings"],
  "jd_role": "role title from JD or inferred from resume",
  "jd_required_skills": ["skills required by the JD, or inferred key skills for the role"],
  "matched_skills": ["skills in both resume and JD requirements"],
  "missing_skills": ["JD skills not clearly present in resume"],
  "resume_summary": "3-4 sentence summary of the candidate"
}}
"""
    data = chat_json(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
        max_tokens=1500,
    )
    # Defensive defaults
    data.setdefault("name", "Candidate")
    data.setdefault("skills", [])
    data.setdefault("projects", [])
    data.setdefault("experience", [])
    data.setdefault("education", [])
    data.setdefault("jd_role", "General Role")
    data.setdefault("jd_required_skills", [])
    data.setdefault("matched_skills", [])
    data.setdefault("missing_skills", [])
    data.setdefault("resume_summary", "")
    return data
