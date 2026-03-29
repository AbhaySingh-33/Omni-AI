"use client";
import { useState } from "react";
import { useInterviewQuestions } from "@/hooks/useInterview";
import { InterviewQuestion } from "@/lib/types";

interface Props {
  token: string;
}

export default function InterviewQuestions({ token }: Props) {
  const { questions, loading, error, generateQuestions } = useInterviewQuestions(token);
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [company, setCompany] = useState("");
  const [interviewType, setInterviewType] = useState("general");
  const [difficulty, setDifficulty] = useState("medium");
  const [expandedQuestion, setExpandedQuestion] = useState<number | null>(null);

  const handleGenerate = async () => {
    if (!jobTitle.trim()) return;
    await generateQuestions({
      job_title: jobTitle,
      job_description: jobDescription || undefined,
      company: company || undefined,
      interview_type: interviewType,
      difficulty,
    });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      technical: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      behavioral: "bg-purple-500/20 text-purple-400 border-purple-500/30",
      situational: "bg-amber-500/20 text-amber-400 border-amber-500/30",
      general: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    };
    return colors[category.toLowerCase()] || colors.general;
  };

  const getDifficultyColor = (diff: string) => {
    const colors: Record<string, string> = {
      easy: "text-green-400",
      medium: "text-amber-400",
      hard: "text-red-400",
    };
    return colors[diff.toLowerCase()] || colors.medium;
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white">❓ Interview Questions</h2>
        <p className="text-white/50 text-sm">Generate tailored interview questions for your target role</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Form */}
      <div className="bg-[#111] border border-white/10 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-white/60 text-sm mb-2">Job Title *</label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g., Software Engineer, Product Manager"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder:text-white/30"
            />
          </div>
          <div>
            <label className="block text-white/60 text-sm mb-2">Company (optional)</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g., Google, Amazon, Startup"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder:text-white/30"
            />
          </div>
        </div>

        <div>
          <label className="block text-white/60 text-sm mb-2">Job Description (optional)</label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={3}
            placeholder="Paste the job description here for more targeted questions..."
            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-white/30 resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-white/60 text-sm mb-2">Interview Type</label>
            <select
              value={interviewType}
              onChange={(e) => setInterviewType(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
            >
              <option value="general">General (Mixed)</option>
              <option value="technical">Technical</option>
              <option value="behavioral">Behavioral</option>
            </select>
          </div>
          <div>
            <label className="block text-white/60 text-sm mb-2">Difficulty</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
            >
              <option value="easy">Entry Level</option>
              <option value="medium">Mid Level</option>
              <option value="hard">Senior Level</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading || !jobTitle.trim()}
          className="w-full px-4 py-3 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Generating Questions...
            </span>
          ) : (
            "✨ Generate Questions"
          )}
        </button>
      </div>

      {/* Questions List */}
      {questions.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">
              📋 Generated Questions ({questions.length})
            </h3>
            <button
              onClick={() => setExpandedQuestion(null)}
              className="text-white/50 hover:text-white text-sm"
            >
              Collapse All
            </button>
          </div>

          <div className="space-y-3">
            {questions.map((q: InterviewQuestion, idx: number) => (
              <div
                key={idx}
                className="bg-[#111] border border-white/10 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setExpandedQuestion(expandedQuestion === idx ? null : idx)}
                  className="w-full p-4 flex items-start gap-4 text-left hover:bg-white/5 transition-colors"
                >
                  <span className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-white/60 text-sm font-medium flex-shrink-0">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium">{q.question}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${getCategoryColor(q.category)}`}>
                        {q.category}
                      </span>
                      <span className={`text-xs ${getDifficultyColor(q.difficulty)}`}>
                        {q.difficulty}
                      </span>
                    </div>
                  </div>
                  <svg
                    className={`w-5 h-5 text-white/40 transition-transform ${expandedQuestion === idx ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {expandedQuestion === idx && (
                  <div className="px-4 pb-4 pt-0 border-t border-white/5 space-y-4">
                    <div className="ml-12">
                      {/* What they look for */}
                      <div className="bg-blue-500/10 rounded-lg p-3 mb-3">
                        <p className="text-blue-400 text-xs font-medium mb-1">👀 What Interviewers Look For</p>
                        <p className="text-white/70 text-sm">{q.what_they_look_for}</p>
                      </div>

                      {/* Sample Answer Points */}
                      {q.sample_answer_points && q.sample_answer_points.length > 0 && (
                        <div className="bg-emerald-500/10 rounded-lg p-3 mb-3">
                          <p className="text-emerald-400 text-xs font-medium mb-2">✅ Key Points for Your Answer</p>
                          <ul className="space-y-1">
                            {q.sample_answer_points.map((point, i) => (
                              <li key={i} className="text-white/70 text-sm flex items-start gap-2">
                                <span className="text-emerald-400">•</span> {point}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Follow-up Questions */}
                      {q.follow_up_questions && q.follow_up_questions.length > 0 && (
                        <div className="bg-amber-500/10 rounded-lg p-3">
                          <p className="text-amber-400 text-xs font-medium mb-2">🔄 Possible Follow-ups</p>
                          <ul className="space-y-1">
                            {q.follow_up_questions.map((fq, i) => (
                              <li key={i} className="text-white/70 text-sm flex items-start gap-2">
                                <span className="text-amber-400">•</span> {fq}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {questions.length === 0 && !loading && (
        <div className="bg-[#111] border border-white/10 rounded-xl p-12 text-center">
          <span className="text-4xl mb-4 block">❓</span>
          <h3 className="text-white font-medium mb-2">No Questions Generated Yet</h3>
          <p className="text-white/50 text-sm">
            Enter a job title above and click generate to get tailored interview questions
          </p>
        </div>
      )}
    </div>
  );
}
