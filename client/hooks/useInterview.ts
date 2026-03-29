"use client";
import { useState, useCallback, useEffect } from "react";
import {
  Resume,
  InterviewSession,
  InterviewFeedback,
  InterviewQuestion,
  UserProgress,
} from "@/lib/types";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

// ============= RESUME HOOK =============
export function useResume(token: string | null) {
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const fetchResume = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/resume`, { headers });
      const data = await res.json();
      setResume(data.resume);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch resume");
    } finally {
      setLoading(false);
    }
  }, [token]);

  const saveResume = useCallback(async (content: string, jobTitle?: string) => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/resume`, {
        method: "POST",
        headers,
        body: JSON.stringify({ content, job_title: jobTitle }),
      });
      const data = await res.json();
      if (data.success) {
        await fetchResume();
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save resume");
    } finally {
      setLoading(false);
    }
  }, [token, fetchResume]);

  const generateResume = useCallback(async (formData: {
    name: string;
    email: string;
    phone?: string;
    linkedin?: string;
    summary?: string;
    experience: { company: string; title: string; startDate: string; endDate?: string; description: string }[];
    education: { institution: string; degree: string; field: string; graduationDate: string }[];
    skills: string[];
    job_title?: string;
  }) => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/resume/generate`, {
        method: "POST",
        headers,
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (data.success) {
        await fetchResume();
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate resume");
    } finally {
      setLoading(false);
    }
  }, [token, fetchResume]);

  const analyzeResume = useCallback(async (content: string, jobTitle?: string) => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/resume/analyze`, {
        method: "POST",
        headers,
        body: JSON.stringify({ content, job_title: jobTitle }),
      });
      return await res.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze resume");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchResume();
  }, [fetchResume]);

  return { resume, loading, error, saveResume, generateResume, analyzeResume, fetchResume };
}

// ============= QUESTIONS HOOK =============
export function useInterviewQuestions(token: string | null) {
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const generateQuestions = useCallback(async (params: {
    job_title: string;
    job_description?: string;
    company?: string;
    interview_type?: string;
    difficulty?: string;
  }) => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/questions`, {
        method: "POST",
        headers,
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.success && data.data?.questions) {
        setQuestions(data.data.questions);
      } else {
        throw new Error("Received invalid format from AI generator.");
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate questions");
    } finally {
      setLoading(false);
    }
  }, [token]);

  return { questions, loading, error, generateQuestions };
}

// ============= MOCK INTERVIEW HOOK =============
export function useMockInterview(token: string | null) {
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const startInterview = useCallback(async (params: {
    job_title: string;
    company?: string;
    interview_type?: string;
  }) => {
    if (!token) return;
    setLoading(true);
    setError(null);
    setMessages([]);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/mock/start`, {
        method: "POST",
        headers,
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.success) {
        setSession({ id: data.session_id, job_title: params.job_title, company: params.company, interview_type: params.interview_type || "general", status: "in_progress", created_at: new Date().toISOString() });
        setMessages([{ role: "interviewer", content: data.message }]);
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start interview");
    } finally {
      setLoading(false);
    }
  }, [token]);

  const respond = useCallback(async (message: string) => {
    if (!token || !session) return;
    setLoading(true);
    setMessages((prev) => [...prev, { role: "candidate", content: message }]);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/mock/respond`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          session_id: session.id,
          message,
          job_title: session.job_title,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setMessages((prev) => [...prev, { role: "interviewer", content: data.message }]);
        if (data.completed) {
          setSession((prev) => prev ? { ...prev, status: "completed" } : null);
        }
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send response");
    } finally {
      setLoading(false);
    }
  }, [token, session]);

  const endInterview = useCallback(() => {
    setSession(null);
    setMessages([]);
  }, []);

  return { session, messages, loading, error, startInterview, respond, endInterview };
}

// ============= FEEDBACK HOOK =============
export function useInterviewFeedback(token: string | null) {
  const [feedback, setFeedback] = useState<InterviewFeedback | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const generateFeedback = useCallback(async (sessionId: number) => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/feedback/${sessionId}`, {
        method: "POST",
        headers,
      });
      const data = await res.json();
      if (data.success) {
        setFeedback(data.feedback);
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate feedback");
    } finally {
      setLoading(false);
    }
  }, [token]);

  const evaluateAnswer = useCallback(async (question: string, answer: string, jobTitle?: string) => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/interview/evaluate-answer`, {
        method: "POST",
        headers,
        body: JSON.stringify({ question, answer, job_title: jobTitle }),
      });
      return await res.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to evaluate answer");
    } finally {
      setLoading(false);
    }
  }, [token]);

  return { feedback, loading, error, generateFeedback, evaluateAnswer };
}

// ============= PROGRESS HOOK =============
export function useInterviewProgress(token: string | null) {
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [loading, setLoading] = useState(false);

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const fetchProgress = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [progressRes, sessionsRes] = await Promise.all([
        fetch(`${AI_ENGINE_URL}/interview/progress`, { headers }),
        fetch(`${AI_ENGINE_URL}/interview/mock/sessions`, { headers }),
      ]);
      const progressData = await progressRes.json();
      const sessionsData = await sessionsRes.json();
      if (progressData.success) setProgress(progressData.progress);
      if (sessionsData.success) setSessions(sessionsData.sessions);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  return { progress, sessions, loading, fetchProgress };
}
