export type Role = "user" | "assistant";

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
  agent?: AgentType;
}

export type AgentType = "reasoning" | "research" | "tools" | "memory" | "router" | "interview";

export interface AgentInfo {
  id: AgentType;
  label: string;
  description: string;
  color: string;
  icon: string;
}

export interface AuthUser {
  email: string;
  token: string;
}

// Interview Prep Types
export interface Resume {
  id: number;
  content: string;
  parsed_data: ResumeData;
  created_at: string;
  updated_at: string;
}

export interface ResumeData {
  name?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  summary?: string;
  experience?: Experience[];
  education?: Education[];
  skills?: string[];
}

export interface Experience {
  company: string;
  title: string;
  startDate: string;
  endDate?: string;
  description: string;
  achievements?: string[];
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  graduationDate: string;
  gpa?: string;
}

export interface InterviewSession {
  id: number;
  job_title: string;
  company?: string;
  interview_type: string;
  status: "in_progress" | "completed";
  created_at: string;
  completed_at?: string;
  overall_score?: number;
  messages?: InterviewMessage[];
}

export interface InterviewMessage {
  id: number;
  role: "interviewer" | "candidate";
  content: string;
  question_number?: number;
  created_at: string;
}

export interface InterviewFeedback {
  id: number;
  overall_score: number;
  communication_score: number;
  content_score: number;
  confidence_score: number;
  strengths: { point: string; example: string }[];
  improvements: { area: string; suggestion: string; example?: string }[];
  detailed_feedback: string;
  created_at: string;
}

export interface InterviewQuestion {
  question: string;
  category: string;
  difficulty: string;
  what_they_look_for: string;
  sample_answer_points: string[];
  follow_up_questions?: string[];
}

export interface UserProgress {
  total_sessions: number;
  completed_sessions: number;
  average_score?: number;
  recent_scores: { score: number; date: string }[];
  has_resume: boolean;
  improvement_trend?: "improving" | "declining" | "stable" | "insufficient_data";
}
