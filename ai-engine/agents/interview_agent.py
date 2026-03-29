"""
Interview Prep Agent - Complete job interview preparation system

This agent handles:
- Resume analysis and improvement
- Interview question generation based on job descriptions
- Mock interview conversations with realistic questions
- Performance feedback and improvement suggestions
"""

from app.gemini import llm
from langchain_core.messages import AIMessage
import json
import re


def interview_agent(state):
    """
    Main interview agent that processes interview-related requests.
    Routes to appropriate sub-function based on the task type.
    """
    messages = state["messages"]
    last_message = messages[-1].content.lower().strip()
    user_id = state.get("user_id")

    # Determine the interview task type
    task_type = _classify_interview_task(last_message)

    if task_type == "resume_create":
        response = _generate_resume(messages[-1].content, user_id)
    elif task_type == "resume_analyze":
        response = _analyze_resume(messages[-1].content, user_id)
    elif task_type == "questions":
        response = _generate_interview_questions(messages[-1].content, user_id)
    elif task_type == "mock_interview":
        response = _conduct_mock_interview(messages, user_id)
    elif task_type == "feedback":
        response = _generate_feedback(messages, user_id)
    else:
        response = _general_interview_help(messages[-1].content)

    return {
        "messages": [AIMessage(content=response)],
        "agent_used": "interview"
    }


def _classify_interview_task(content: str) -> str:
    """Classify the type of interview preparation task."""
    content_lower = content.lower()

    # Resume creation keywords
    if any(kw in content_lower for kw in ["create resume", "build resume", "make resume",
                                           "generate resume", "write resume", "new resume"]):
        return "resume_create"

    # Resume analysis keywords
    if any(kw in content_lower for kw in ["review resume", "analyze resume", "improve resume",
                                           "resume feedback", "check resume", "resume tips"]):
        return "resume_analyze"

    # Interview question keywords
    if any(kw in content_lower for kw in ["interview question", "prepare question",
                                           "what questions", "common questions", "technical questions",
                                           "behavioral questions", "practice questions"]):
        return "questions"

    # Mock interview keywords
    if any(kw in content_lower for kw in ["mock interview", "practice interview",
                                           "interview me", "simulate interview", "interview practice",
                                           "start interview", "begin interview"]):
        return "mock_interview"

    # Feedback keywords
    if any(kw in content_lower for kw in ["how did i do", "interview feedback",
                                           "my performance", "evaluate my", "rate my answer",
                                           "feedback on", "score my"]):
        return "feedback"

    return "general"


def _generate_resume(user_input: str, user_id: str) -> str:
    """Generate a professional resume based on user's information."""
    prompt = f"""You are a professional resume writer with expertise in creating ATS-friendly resumes.

Based on the user's input, create a comprehensive, professional resume. If the user hasn't provided enough information, ask clarifying questions.

User Input: {user_input}

Instructions:
1. If sufficient info is provided, generate a complete resume in a clean, professional format
2. Use strong action verbs and quantifiable achievements
3. Organize sections: Contact Info, Summary, Experience, Skills, Education
4. Make it ATS-friendly with relevant keywords
5. If info is missing, ask specific questions about: role, experience, skills, education, achievements

Generate the resume or ask for needed information:"""

    result = llm.invoke(prompt)
    return result.content


def _analyze_resume(user_input: str, user_id: str) -> str:
    """Analyze and provide improvement suggestions for a resume."""
    prompt = f"""You are an expert resume reviewer and career coach.

Analyze the provided resume and give detailed, actionable feedback.

Resume Content: {user_input}

Provide analysis in these categories:

## Overall Score: X/10

## Strengths
- List 3-5 strong points

## Areas for Improvement
- List specific, actionable improvements

## ATS Optimization
- Keywords to add
- Formatting suggestions

## Impact Enhancement
- How to make achievements more quantifiable
- Stronger action verbs to use

## Industry-Specific Tips
- Relevant certifications or skills to highlight

Be specific and constructive. Help the user create a winning resume."""

    result = llm.invoke(prompt)
    return result.content


def _generate_interview_questions(user_input: str, user_id: str) -> str:
    """Generate tailored interview questions based on job description and role."""
    prompt = f"""You are a senior hiring manager and interview expert.

Based on the user's request, generate comprehensive interview questions.

User Request: {user_input}

Generate questions in these categories:

## Technical Questions (5 questions)
- Role-specific technical questions
- Include expected good answers

## Behavioral Questions (5 questions)
- STAR method questions
- Include what interviewers look for

## Situational Questions (3 questions)
- Hypothetical scenarios
- Include how to approach the answer

## Company/Culture Fit Questions (3 questions)
- Questions about motivation and fit

## Questions to Ask the Interviewer (3 questions)
- Smart questions that show engagement

For each question, provide:
1. The question itself
2. Why it's asked
3. Key points to include in a strong answer

Make questions specific to the role/industry mentioned."""

    result = llm.invoke(prompt)
    return result.content


def _conduct_mock_interview(messages: list, user_id: str) -> str:
    """Conduct an interactive mock interview session."""
    # Build conversation context
    conversation_history = ""
    for msg in messages[-10:]:  # Last 10 messages for context
        role = "Interviewer" if hasattr(msg, 'type') and msg.type == "ai" else "Candidate"
        conversation_history += f"{role}: {msg.content}\n"

    # Check if this is the start of a mock interview
    last_message = messages[-1].content.lower()
    is_start = any(kw in last_message for kw in ["start", "begin", "mock interview", "practice interview"])

    if is_start:
        prompt = f"""You are a professional interviewer conducting a mock interview.

The candidate wants to practice interviewing. Based on their message, determine:
1. What role they're interviewing for
2. What type of interview (technical, behavioral, etc.)

User Message: {messages[-1].content}

Start the mock interview:
1. Greet them professionally
2. Briefly explain the interview format
3. Ask your first interview question

Be realistic, professional, and encouraging. This should feel like a real interview.

If the role isn't clear, ask what position they're preparing for."""
    else:
        prompt = f"""You are conducting a mock interview. Continue the interview naturally.

Interview History:
{conversation_history}

The candidate just responded. As the interviewer:
1. Acknowledge their answer briefly (don't over-praise)
2. If appropriate, ask a follow-up question OR move to next topic
3. Keep the interview flowing naturally
4. After 5-7 questions, wrap up the interview and indicate you'll provide feedback

Be professional, realistic, and helpful. Simulate a real interview experience."""

    result = llm.invoke(prompt)
    return result.content


def _generate_feedback(messages: list, user_id: str) -> str:
    """Generate comprehensive feedback on interview performance."""
    # Collect interview conversation
    conversation = ""
    for msg in messages[-20:]:  # Get more context for feedback
        role = "Interviewer" if hasattr(msg, 'type') and msg.type == "ai" else "Candidate"
        conversation += f"{role}: {msg.content}\n"

    prompt = f"""You are an expert interview coach providing detailed feedback.

Review this mock interview conversation and provide comprehensive feedback:

{conversation}

## Overall Performance Score: X/10

## Communication Skills
- Clarity and articulation
- Confidence level
- Professional tone

## Content Quality
- Relevance of answers
- Use of examples/STAR method
- Technical accuracy

## Strengths Demonstrated
- List 3-5 specific strong points with examples

## Areas for Improvement
- List specific areas to work on
- Provide actionable tips for each

## Answer-by-Answer Analysis
For each major answer, provide:
- What was done well
- What could be improved
- Suggested better response approach

## Recommended Next Steps
1. Immediate actions to take
2. Skills to develop
3. Practice exercises

Be constructive, specific, and encouraging. Help the candidate improve."""

    result = llm.invoke(prompt)
    return result.content


def _general_interview_help(user_input: str) -> str:
    """Provide general interview preparation assistance."""
    prompt = f"""You are a career coach and interview preparation expert.

Help the user with their interview-related question.

User Question: {user_input}

Provide helpful, actionable advice. Cover topics like:
- Interview preparation strategies
- Common mistakes to avoid
- Industry-specific tips
- Confidence-building techniques
- Follow-up best practices

Be encouraging and practical. If the question is vague, offer to help with:
1. Creating or improving their resume
2. Generating practice interview questions
3. Conducting a mock interview
4. Providing feedback on their interview skills

Guide them toward the most helpful next step."""

    result = llm.invoke(prompt)
    return result.content


# Keywords for router agent to detect interview-related queries
INTERVIEW_KEYWORDS = [
    "interview", "resume", "cv", "job", "hire", "hiring", "career",
    "job search", "job hunt", "apply", "application", "candidate",
    "recruiter", "hr", "mock interview", "practice interview",
    "behavioral question", "technical interview", "salary negotiation",
    "cover letter", "linkedin", "portfolio", "job offer", "employed",
    "unemployment", "position", "role", "company", "workplace"
]
