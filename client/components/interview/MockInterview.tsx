"use client";
import { useState, useRef, useEffect } from "react";
import { useMockInterview, useInterviewFeedback } from "@/hooks/useInterview";

interface Props {
  token: string;
}

export default function MockInterview({ token }: Props) {
  const { session, messages, loading, startInterview, respond, endInterview } = useMockInterview(token);
  const { feedback, loading: feedbackLoading, generateFeedback } = useInterviewFeedback(token);

  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [interviewType, setInterviewType] = useState("general");
  const [userInput, setUserInput] = useState("");
  const [showFeedback, setShowFeedback] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStart = async () => {
    if (!jobTitle.trim()) return;
    await startInterview({
      job_title: jobTitle,
      company: company || undefined,
      interview_type: interviewType,
    });
  };

  const handleSend = async () => {
    if (!userInput.trim() || loading) return;
    const message = userInput;
    setUserInput("");
    await respond(message);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleGetFeedback = async () => {
    if (!session) return;
    await generateFeedback(session.id);
    setShowFeedback(true);
  };

  const handleEndAndRestart = () => {
    endInterview();
    setShowFeedback(false);
    setJobTitle("");
    setCompany("");
  };

  // Setup View
  if (!session) {
    return (
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white">🎤 Mock Interview</h2>
          <p className="text-white/50 text-sm">Practice with a realistic AI interviewer</p>
        </div>

        <div className="bg-[#111] border border-white/10 rounded-xl p-6 space-y-4">
          <div className="text-center py-6">
            <span className="text-5xl mb-4 block">🎯</span>
            <h3 className="text-white font-semibold text-lg mb-2">Ready to Practice?</h3>
            <p className="text-white/50 text-sm mb-6">
              Our AI interviewer will conduct a realistic mock interview and provide detailed feedback
            </p>
          </div>

          <div>
            <label className="block text-white/60 text-sm mb-2">Job Title *</label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g., Software Engineer, Data Scientist"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder:text-white/30"
            />
          </div>

          <div>
            <label className="block text-white/60 text-sm mb-2">Company (optional)</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g., Google, Amazon, Your Target Company"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder:text-white/30"
            />
          </div>

          <div>
            <label className="block text-white/60 text-sm mb-2">Interview Type</label>
            <select
              value={interviewType}
              onChange={(e) => setInterviewType(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
            >
              <option value="general">General (Mixed Questions)</option>
              <option value="technical">Technical Interview</option>
              <option value="behavioral">Behavioral Interview</option>
            </select>
          </div>

          <button
            onClick={handleStart}
            disabled={loading || !jobTitle.trim()}
            className="w-full px-4 py-3 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors disabled:opacity-50"
          >
            {loading ? "Starting Interview..." : "🚀 Start Mock Interview"}
          </button>

          <div className="pt-4 border-t border-white/10">
            <p className="text-white/40 text-xs text-center">
              💡 Tip: Answer as you would in a real interview. Be specific and use examples.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Feedback View
  if (showFeedback && feedback) {
    return (
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">📊 Interview Feedback</h2>
            <p className="text-white/50 text-sm">{session.job_title} at {session.company || "Company"}</p>
          </div>
          <button
            onClick={handleEndAndRestart}
            className="px-4 py-2 bg-white/10 text-white rounded-lg text-sm hover:bg-white/20"
          >
            Start New Interview
          </button>
        </div>

        {/* Scores */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <ScoreCard label="Overall" score={feedback.overall_score} color="purple" />
          <ScoreCard label="Communication" score={feedback.communication_score} color="blue" />
          <ScoreCard label="Content" score={feedback.content_score} color="emerald" />
          <ScoreCard label="Confidence" score={feedback.confidence_score} color="amber" />
        </div>

        {/* Strengths */}
        {feedback.strengths && feedback.strengths.length > 0 && (
          <div className="bg-[#111] border border-white/10 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-3">✅ Strengths</h3>
            <div className="space-y-3">
              {feedback.strengths.map((s, i) => (
                <div key={i} className="bg-green-500/10 rounded-lg p-3">
                  <p className="text-green-400 font-medium text-sm">{s.point}</p>
                  {s.example && <p className="text-white/60 text-sm mt-1">&quot;{s.example}&quot;</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Improvements */}
        {feedback.improvements && feedback.improvements.length > 0 && (
          <div className="bg-[#111] border border-white/10 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-3">📝 Areas for Improvement</h3>
            <div className="space-y-3">
              {feedback.improvements.map((imp, i) => (
                <div key={i} className="bg-amber-500/10 rounded-lg p-3">
                  <p className="text-amber-400 font-medium text-sm">{imp.area}</p>
                  <p className="text-white/60 text-sm mt-1">{imp.suggestion}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Feedback */}
        {feedback.detailed_feedback && (
          <div className="bg-[#111] border border-white/10 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-3">📋 Detailed Analysis</h3>
            <pre className="whitespace-pre-wrap text-white/70 text-sm leading-relaxed">
              {feedback.detailed_feedback}
            </pre>
          </div>
        )}
      </div>
    );
  }

  // Interview Chat View
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 bg-[#0d0d0d] flex items-center justify-between">
        <div>
          <h2 className="text-white font-semibold">🎤 Mock Interview in Progress</h2>
          <p className="text-white/50 text-sm">
            {session.job_title} {session.company ? `at ${session.company}` : ""} • {session.interview_type}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {session.status === "completed" ? (
            <button
              onClick={handleGetFeedback}
              disabled={feedbackLoading}
              className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm font-medium hover:bg-purple-600 disabled:opacity-50"
            >
              {feedbackLoading ? "Getting Feedback..." : "📊 Get Feedback"}
            </button>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400/70 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live
            </div>
          )}
          <button
            onClick={handleEndAndRestart}
            className="px-3 py-2 text-white/50 hover:text-white text-sm"
          >
            End
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "candidate" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "candidate"
                  ? "bg-purple-500/20 text-white border border-purple-500/30"
                  : "bg-white/10 text-white border border-white/10"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium opacity-60">
                  {msg.role === "candidate" ? "You" : "Interviewer"}
                </span>
              </div>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white/10 rounded-2xl px-4 py-3 border border-white/10">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-white/40 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-white/40 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                <div className="w-2 h-2 bg-white/40 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      {session.status !== "completed" && (
        <div className="p-4 border-t border-white/10 bg-[#0d0d0d]">
          <div className="flex gap-3 max-w-3xl mx-auto">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your answer..."
              rows={2}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30 resize-none focus:outline-none focus:border-purple-500/50"
            />
            <button
              onClick={handleSend}
              disabled={loading || !userInput.trim()}
              className="px-6 bg-purple-500 text-white rounded-xl font-medium hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
          <p className="text-white/30 text-xs text-center mt-2">
            Press Enter to send • Shift+Enter for new line
          </p>
        </div>
      )}

      {/* Completed state */}
      {session.status === "completed" && (
        <div className="p-4 border-t border-white/10 bg-[#0d0d0d] text-center">
          <p className="text-white/50 text-sm mb-3">Interview completed! 🎉</p>
          <button
            onClick={handleGetFeedback}
            disabled={feedbackLoading}
            className="px-6 py-3 bg-purple-500 text-white rounded-xl font-medium hover:bg-purple-600 disabled:opacity-50"
          >
            {feedbackLoading ? "Generating Feedback..." : "📊 Get Detailed Feedback"}
          </button>
        </div>
      )}
    </div>
  );
}

function ScoreCard({ label, score, color }: { label: string; score: number; color: string }) {
  const colorMap: Record<string, string> = {
    purple: "bg-purple-500/20 border-purple-500/30 text-purple-400",
    blue: "bg-blue-500/20 border-blue-500/30 text-blue-400",
    emerald: "bg-emerald-500/20 border-emerald-500/30 text-emerald-400",
    amber: "bg-amber-500/20 border-amber-500/30 text-amber-400",
  };

  return (
    <div className={`${colorMap[color]} border rounded-xl p-4 text-center`}>
      <p className="text-2xl font-bold">{score || "N/A"}/10</p>
      <p className="text-white/50 text-xs mt-1">{label}</p>
    </div>
  );
}
