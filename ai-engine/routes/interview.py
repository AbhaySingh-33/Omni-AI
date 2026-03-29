"""
Interview Prep API Routes

Endpoints for:
- Resume management (CRUD)
- Interview question generation
- Mock interview sessions
- Feedback and analytics
- PDF resume download
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
import json
import io
import re

from app.auth import get_current_user
from app.gemini import llm
from services.interview import (
    save_resume, get_resume, get_all_resumes, delete_resume,
    create_interview_session, save_interview_message, get_interview_session,
    get_user_sessions, complete_interview_session, save_feedback,
    get_feedback, get_user_progress, init_interview_tables
)

router = APIRouter(prefix="/interview", tags=["interview"])


# ============= REQUEST MODELS =============

class ResumeRequest(BaseModel):
    content: str
    job_title: Optional[str] = None
    target_company: Optional[str] = None


class ResumeGenerateRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    summary: Optional[str] = None
    experience: List[dict] = []
    education: List[dict] = []
    skills: List[str] = []
    job_title: Optional[str] = None  # Target job for tailoring


class QuestionRequest(BaseModel):
    job_title: str
    job_description: Optional[str] = None
    company: Optional[str] = None
    interview_type: str = "general"  # general, technical, behavioral
    difficulty: str = "medium"  # easy, medium, hard


class MockInterviewRequest(BaseModel):
    job_title: str
    company: Optional[str] = None
    interview_type: str = "general"
    session_id: Optional[int] = None  # For continuing existing session
    message: Optional[str] = None  # User's response


class AnswerEvaluateRequest(BaseModel):
    question: str
    answer: str
    job_title: Optional[str] = None


# ============= RESUME ENDPOINTS =============

@router.post("/resume")
async def create_or_update_resume(req: ResumeRequest, user=Depends(get_current_user)):
    """Save or update user's resume."""
    resume_data = {
        "content": req.content,
        "job_title": req.job_title,
        "target_company": req.target_company
    }
    resume_id = save_resume(user["user_id"], resume_data)
    return {"success": True, "resume_id": resume_id}


@router.post("/resume/generate")
async def generate_resume(req: ResumeGenerateRequest, user=Depends(get_current_user)):
    """Generate a professional resume from structured data."""
    prompt = f"""Create a professional, ATS-friendly resume for:

Name: {req.name}
Email: {req.email}
Phone: {req.phone or 'Not provided'}
LinkedIn: {req.linkedin or 'Not provided'}

Professional Summary: {req.summary or 'Generate based on experience'}

Experience:
{json.dumps(req.experience, indent=2) if req.experience else 'No experience provided'}

Education:
{json.dumps(req.education, indent=2) if req.education else 'No education provided'}

Skills: {', '.join(req.skills) if req.skills else 'Not provided'}

Target Position: {req.job_title or 'General'}

Instructions:
1. Create a clean, professional resume format
2. Use strong action verbs and quantifiable achievements
3. Optimize for ATS with relevant keywords
4. Keep it concise (1-2 pages equivalent)
5. Format with clear sections using markdown

Generate the resume:"""

    result = llm.invoke(prompt)
    resume_content = result.content

    # Save the generated resume
    resume_data = {
        "content": resume_content,
        "job_title": req.job_title,
        "parsed_data": {
            "name": req.name,
            "email": req.email,
            "experience": req.experience,
            "education": req.education,
            "skills": req.skills
        }
    }
    resume_id = save_resume(user["user_id"], resume_data)

    return {
        "success": True,
        "resume_id": resume_id,
        "content": resume_content
    }


@router.post("/resume/analyze")
async def analyze_resume(req: ResumeRequest, user=Depends(get_current_user)):
    """Analyze resume and provide improvement suggestions."""
    prompt = f"""You are an expert resume reviewer and ATS optimization specialist.

Analyze this resume for someone targeting: {req.job_title or 'general positions'}
{f'at {req.target_company}' if req.target_company else ''}

Resume:
{req.content}

Provide a comprehensive analysis in JSON format:
{{
    "overall_score": <1-10>,
    "ats_score": <1-10>,
    "strengths": ["list", "of", "strengths"],
    "improvements": ["specific", "actionable", "improvements"],
    "missing_keywords": ["keywords", "to", "add"],
    "format_issues": ["formatting", "problems"],
    "content_suggestions": {{
        "summary": "suggestion for summary section",
        "experience": "suggestions for experience section",
        "skills": "suggestions for skills section"
    }},
    "quick_wins": ["easy", "high-impact", "changes"]
}}

Be specific and actionable in your feedback."""

    result = llm.invoke(prompt)

    # Try to parse as JSON, fall back to text
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', result.content)
        if json_match:
            json_str = json_match.group()
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            analysis = json.loads(json_str)
        else:
            analysis = {"raw_feedback": result.content}
    except json.JSONDecodeError:
        analysis = {"raw_feedback": result.content}

    return {
        "success": True,
        "analysis": analysis,
        "raw_response": result.content
    }


@router.get("/resume")
async def get_user_resume(user=Depends(get_current_user)):
    """Get user's latest resume."""
    resume = get_resume(user["user_id"])
    if not resume:
        return {"success": True, "resume": None}
    return {"success": True, "resume": resume}


@router.get("/resume/all")
async def get_user_resumes(user=Depends(get_current_user)):
    """Get all resumes for a user."""
    resumes = get_all_resumes(user["user_id"])
    return {"success": True, "resumes": resumes}


@router.delete("/resume/{resume_id}")
async def remove_resume(resume_id: int, user=Depends(get_current_user)):
    """Delete a specific resume."""
    deleted = delete_resume(user["user_id"], resume_id)
    return {"success": deleted}


# ============= QUESTIONS ENDPOINTS =============

@router.post("/questions")
async def generate_questions(req: QuestionRequest, user=Depends(get_current_user)):
    """Generate tailored interview questions."""
    type_focus = {
        "general": "a mix of behavioral, situational, and general questions",
        "technical": "technical and problem-solving questions specific to the role",
        "behavioral": "behavioral questions using the STAR method format"
    }.get(req.interview_type, "a mix of question types")

    difficulty_guide = {
        "easy": "entry-level/junior positions",
        "medium": "mid-level positions with some experience required",
        "hard": "senior/leadership positions with complex scenarios"
    }.get(req.difficulty, "mid-level positions")

    prompt = f"""You are a senior hiring manager creating interview questions.

Generate interview questions for:
- Position: {req.job_title}
- Company: {req.company or 'General'}
- Type: {type_focus}
- Difficulty: {difficulty_guide}

{f'Job Description: {req.job_description}' if req.job_description else ''}

Return in JSON format:
{{
    "questions": [
        {{
            "question": "The interview question",
            "category": "technical/behavioral/situational/general",
            "difficulty": "easy/medium/hard",
            "what_they_look_for": "What the interviewer wants to hear",
            "sample_answer_points": ["Key point 1", "Key point 2"],
            "follow_up_questions": ["Potential follow-up 1"]
        }}
    ],
    "tips": ["General tips for this type of interview"],
    "red_flags_to_avoid": ["Things that would concern interviewers"]
}}

Generate 10-15 relevant questions."""

    result = llm.invoke(prompt)

    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', result.content)
        if json_match:
            json_str = json_match.group()
            # Clean up trailing commas that break standard json.loads
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            questions_data = json.loads(json_str)
        else:
            questions_data = {"raw_response": result.content}
    except json.JSONDecodeError as dict_err:
        print(f"JSON Parse Error: {dict_err} - raw result: {result.content}")
        questions_data = {"raw_response": result.content}

    return {
        "success": True,
        "data": questions_data,
        "job_title": req.job_title,
        "interview_type": req.interview_type
    }


# ============= MOCK INTERVIEW ENDPOINTS =============

@router.post("/mock/start")
async def start_mock_interview(req: MockInterviewRequest, user=Depends(get_current_user)):
    """Start a new mock interview session."""
    # Create session
    session_id = create_interview_session(
        user["user_id"],
        req.job_title,
        req.company,
        req.interview_type
    )

    # Generate opening
    prompt = f"""You are a professional interviewer conducting a mock interview.

Position: {req.job_title}
Company: {req.company or 'a leading company'}
Interview Type: {req.interview_type}

Start the interview:
1. Introduce yourself as the interviewer
2. Briefly explain the interview format
3. Make the candidate comfortable
4. Ask your first question

Be professional, realistic, and encouraging."""

    result = llm.invoke(prompt)
    opening = result.content

    # Save interviewer message
    save_interview_message(session_id, "interviewer", opening, question_number=1)

    return {
        "success": True,
        "session_id": session_id,
        "message": opening,
        "question_number": 1
    }


@router.post("/mock/respond")
async def respond_in_mock(req: MockInterviewRequest, user=Depends(get_current_user)):
    """Continue a mock interview with candidate's response."""
    if not req.session_id or not req.message:
        raise HTTPException(status_code=400, detail="session_id and message required")

    # Get session for context
    session = get_interview_session(req.session_id, user["user_id"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save candidate response
    question_num = len([m for m in session["messages"] if m["role"] == "interviewer"])
    save_interview_message(req.session_id, "candidate", req.message, question_number=question_num)

    # Build conversation context
    context = "\n".join([
        f"{'Interviewer' if m['role'] == 'interviewer' else 'Candidate'}: {m['content']}"
        for m in session["messages"][-6:]  # Last 6 messages
    ])

    # Check if we should end the interview
    should_end = question_num >= 6

    if should_end:
        prompt = f"""You are conducting a mock interview that is now concluding.

Interview so far:
{context}

Candidate's latest response: {req.message}

End the interview professionally:
1. Thank the candidate for their time
2. Give a brief positive note
3. Explain that detailed feedback will be provided
4. Close professionally

Keep it brief and encouraging."""
    else:
        prompt = f"""You are conducting a mock interview for a {session['job_title']} position.

Interview so far:
{context}

Candidate's latest response: {req.message}

As the interviewer:
1. Briefly acknowledge their answer (naturally, don't over-praise)
2. Ask the next relevant question
3. Make it conversational and realistic
4. Progress through different question types

Keep it professional and realistic."""

    result = llm.invoke(prompt)
    response = result.content

    # Save interviewer response
    save_interview_message(req.session_id, "interviewer", response, question_number=question_num + 1)

    if should_end:
        complete_interview_session(req.session_id, user["user_id"])

    return {
        "success": True,
        "session_id": req.session_id,
        "message": response,
        "question_number": question_num + 1,
        "completed": should_end
    }


@router.get("/mock/session/{session_id}")
async def get_mock_session(session_id: int, user=Depends(get_current_user)):
    """Get a specific mock interview session."""
    session = get_interview_session(session_id, user["user_id"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "session": session}


@router.get("/mock/sessions")
async def get_mock_sessions(user=Depends(get_current_user)):
    """Get all mock interview sessions for user."""
    sessions = get_user_sessions(user["user_id"])
    return {"success": True, "sessions": sessions}


# ============= FEEDBACK ENDPOINTS =============

@router.post("/feedback/{session_id}")
async def generate_session_feedback(session_id: int, user=Depends(get_current_user)):
    """Generate detailed feedback for a completed mock interview."""
    session = get_interview_session(session_id, user["user_id"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build conversation for analysis
    conversation = "\n".join([
        f"{'Interviewer' if m['role'] == 'interviewer' else 'Candidate'}: {m['content']}"
        for m in session["messages"]
    ])

    prompt = f"""You are an expert interview coach providing detailed feedback.

Mock Interview for: {session['job_title']} at {session.get('company', 'Company')}

Full Conversation:
{conversation}

Provide comprehensive feedback in JSON format:
{{
    "overall_score": <1-10>,
    "communication_score": <1-10>,
    "content_score": <1-10>,
    "confidence_score": <1-10>,
    "strengths": [
        {{"point": "strength description", "example": "specific example from interview"}}
    ],
    "improvements": [
        {{"area": "area to improve", "suggestion": "how to improve", "example": "better response"}}
    ],
    "answer_analysis": [
        {{
            "question_summary": "brief question",
            "score": <1-10>,
            "what_worked": "positive aspects",
            "what_to_improve": "suggestion"
        }}
    ],
    "ready_for_real_interview": true/false,
    "recommended_practice": ["specific practice recommendations"],
    "summary": "2-3 sentence overall summary"
}}

Be constructive, specific, and encouraging."""

    result = llm.invoke(prompt)

    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', result.content)
        if json_match:
            json_str = json_match.group()
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            feedback_data = json.loads(json_str)
        else:
            feedback_data = {"detailed_feedback": result.content, "overall_score": 7}
    except json.JSONDecodeError:
        feedback_data = {"detailed_feedback": result.content, "overall_score": 7}

    # Save feedback
    save_feedback(session_id, user["user_id"], feedback_data)

    # Update session score
    if "overall_score" in feedback_data:
        complete_interview_session(session_id, user["user_id"], feedback_data["overall_score"])

    return {
        "success": True,
        "feedback": feedback_data
    }


@router.get("/feedback/{session_id}")
async def get_session_feedback(session_id: int, user=Depends(get_current_user)):
    """Get feedback for a specific session."""
    feedback = get_feedback(session_id, user["user_id"])
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"success": True, "feedback": feedback}


@router.post("/evaluate-answer")
async def evaluate_single_answer(req: AnswerEvaluateRequest, user=Depends(get_current_user)):
    """Evaluate a single interview answer."""
    prompt = f"""Evaluate this interview answer:

Question: {req.question}
{f'For position: {req.job_title}' if req.job_title else ''}

Candidate's Answer: {req.answer}

Provide evaluation in JSON:
{{
    "score": <1-10>,
    "strengths": ["what was good"],
    "improvements": ["what could be better"],
    "sample_better_answer": "An improved version of the answer",
    "tips": ["specific tips for this type of question"]
}}"""

    result = llm.invoke(prompt)

    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', result.content)
        if json_match:
            evaluation = json.loads(json_match.group())
        else:
            evaluation = {"feedback": result.content}
    except json.JSONDecodeError:
        evaluation = {"feedback": result.content}

    return {"success": True, "evaluation": evaluation}


# ============= PROGRESS & ANALYTICS ENDPOINTS =============

@router.get("/progress")
async def get_interview_progress(user=Depends(get_current_user)):
    """Get user's interview preparation progress and statistics."""
    progress = get_user_progress(user["user_id"])
    return {"success": True, "progress": progress}


# ============= INITIALIZATION =============

@router.post("/init-db")
async def initialize_database(user=Depends(get_current_user)):
    """Initialize interview prep database tables."""
    try:
        init_interview_tables()
        return {"success": True, "message": "Tables initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= PDF GENERATION =============

def _sanitize_text_for_pdf(text: str) -> str:
    """Replace special Unicode characters with ASCII equivalents for PDF."""
    replacements = {
        ''': "'", ''': "'", '"': '"', '"': '"',
        '–': '-', '—': '-', '…': '...', '•': '-',
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u2022': '-',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode('ascii', 'ignore').decode('ascii')


def _is_placeholder(text: str) -> bool:
    """Check if text is a placeholder or AI instruction."""
    placeholders = [
        '[your', '[add', '[list', '[insert', '[include', '[optional',
        '(add if', '(optional', '(e.g.', '(highlight', '(list',
        'add if available', 'if applicable', 'see suggestions',
        'tailor the resume', 'add more projects',
        'ats optimization', 'key ats', 'tips applied', 'optimization tips',
        "here's your", "here is your", "i've created", "i have created",
        'would you like', 'let me know', 'feel free to',
        'keywords:', 'action ver', 'quantifiable', 'suggestions to improve',
        'projects over experience', 'include a github', 'even if private',
        'tech stack:', 'tools/frameworks', 'clean formatting', 'clear sections',
        'bullet points', 'consistent spacing', 'readability'
    ]
    lower = text.lower()
    return any(p in lower for p in placeholders)


def _parse_resume_content(content: str) -> dict:
    """Parse markdown resume content into structured sections."""
    content = _sanitize_text_for_pdf(content)

    sections = {'name': '', 'contact': [], 'sections': []}
    lines = content.split('\n')
    current_section = None
    current_items = []

    # Section header keywords
    section_keywords = [
        'PROFESSIONAL SUMMARY', 'SUMMARY', 'OBJECTIVE',
        'EDUCATION', 'ACADEMIC',
        'EXPERIENCE', 'WORK EXPERIENCE', 'EMPLOYMENT',
        'TECHNICAL SKILLS', 'SKILLS', 'CORE COMPETENCIES',
        'PROJECTS', 'KEY PROJECTS',
        'CERTIFICATIONS', 'CERTIFICATES', 'TRAINING',
        'ACHIEVEMENTS', 'ACCOMPLISHMENTS', 'AWARDS',
        'EXTRACURRICULAR', 'ACTIVITIES',
        'ADDITIONAL', 'OTHER',
        'LANGUAGES', 'PUBLICATIONS', 'REFERENCES'
    ]

    for line in lines:
        original_line = line
        # Clean markdown but preserve content
        line = re.sub(r'^#{1,6}\s*', '', line)  # Remove # headers
        line = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', line)  # Remove bold/italic
        line = line.strip()

        if not line or len(line) < 2:
            continue

        # Skip AI commentary and placeholders
        if _is_placeholder(line):
            continue
        if any(skip in line.lower() for skip in ["here's", "note:", "---", "```"]):
            continue

        # Check if this is a section header
        upper_line = line.upper()
        is_section = False
        matched_section = None

        for kw in section_keywords:
            if kw in upper_line and len(line) < 50:
                is_section = True
                matched_section = kw
                break

        if is_section:
            # Save previous section
            if current_section and current_items:
                sections['sections'].append({'title': current_section, 'items': current_items})
            current_section = matched_section
            current_items = []
            continue

        # Name detection - first non-section, non-contact line before any section
        if not sections['name'] and not current_section:
            # Check if it looks like a name
            if (len(line) < 40 and
                '@' not in line and
                'linkedin' not in line.lower() and
                'github' not in line.lower() and
                not re.search(r'\d{5,}', line) and
                not any(kw in line.upper() for kw in section_keywords)):
                sections['name'] = line
                continue

        # Contact detection - before sections start
        if not current_section:
            # Check for email
            if '@' in line:
                parts = re.split(r'\s*[|]\s*|\s{2,}', line)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 3 and not _is_placeholder(part):
                        sections['contact'].append(part)
                continue

            # Check for phone number
            if re.search(r'\+?\d[\d\s()-]{8,}', line):
                parts = re.split(r'\s*[|]\s*|\s{2,}', line)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 3 and not _is_placeholder(part):
                        sections['contact'].append(part)
                continue

            # Check for LinkedIn/GitHub
            if 'linkedin' in line.lower() or 'github' in line.lower():
                parts = re.split(r'\s*[|]\s*|\s{2,}', line)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 3 and not _is_placeholder(part):
                        sections['contact'].append(part)
                continue

        # Regular content under a section
        if current_section:
            # Clean bullet markers
            clean = line
            if clean.startswith('- ') or clean.startswith('* '):
                clean = clean[2:].strip()

            if clean and len(clean) > 2 and not _is_placeholder(clean):
                current_items.append(clean)

    # Add last section
    if current_section and current_items:
        sections['sections'].append({'title': current_section, 'items': current_items})

    return sections


@router.get("/resume/pdf")
async def download_resume_pdf(user=Depends(get_current_user)):
    """Generate and download resume as PDF with professional formatting."""
    resume = get_resume(user["user_id"])
    if not resume or not resume.get("content"):
        raise HTTPException(status_code=404, detail="No resume found. Create one first.")

    try:
        from fpdf import FPDF
        from markdown_it import MarkdownIt

        raw_content = resume["content"]

        # Extract content from inside code blocks (the actual resume is often inside ```markdown...```)
        code_block_match = re.search(r'```(?:markdown)?\s*([\s\S]*?)```', raw_content)
        if code_block_match:
            content = code_block_match.group(1)
        else:
            content = raw_content

        # Clean content
        content = re.sub(r'^---+$', '', content, flags=re.MULTILINE)  # Remove horizontal rules
        content = re.sub(r'^\*{3,}$', '', content, flags=re.MULTILINE)  # Remove *** lines
        content = _sanitize_text_for_pdf(content)
        
        # Replace large gaps of spaces that might push text off the page
        content = re.sub(r' {4,}', ' ', content)

        md = MarkdownIt()
        html_content = md.render(content)

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_margins(left=20, top=15, right=20)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Set base font before writing HTML
        pdf.set_font("Helvetica", size=11)
        
        pdf.write_html(html_content)

        pdf_bytes = pdf.output()

        return Response(
            content=bytes(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=resume.pdf"}
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="Library missing. Run: pip install fpdf2 markdown-it-py")
    except Exception as e:
        import traceback
        print(f"PDF Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
