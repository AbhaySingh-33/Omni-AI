"use client";
import { useInterviewProgress } from "@/hooks/useInterview";

interface Props {
  token: string;
}

export default function InterviewDashboard({ token }: Props) {
  const { progress, sessions, loading } = useInterviewProgress(token);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case "improving": return "📈";
      case "declining": return "📉";
      case "stable": return "➡️";
      default: return "📊";
    }
  };

  const getTrendColor = (trend?: string) => {
    switch (trend) {
      case "improving": return "text-green-400";
      case "declining": return "text-red-400";
      default: return "text-white/50";
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 rounded-2xl p-6">
        <h2 className="text-2xl font-bold text-white mb-2">🎯 Your Interview Prep Hub</h2>
        <p className="text-white/60">
          OmniAI is your complete AI interview coach. Create resumes, practice questions,
          take mock interviews, and get detailed feedback to land your dream job.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon="📄"
          label="Resume"
          value={progress?.has_resume ? "Ready" : "Not Created"}
          subtext={progress?.has_resume ? "Your resume is on file" : "Create one to get started"}
          color="blue"
        />
        <StatCard
          icon="🎤"
          label="Mock Interviews"
          value={progress?.completed_sessions?.toString() || "0"}
          subtext={`${progress?.total_sessions || 0} total sessions`}
          color="purple"
        />
        <StatCard
          icon="⭐"
          label="Average Score"
          value={progress?.average_score ? `${progress.average_score.toFixed(1)}/10` : "N/A"}
          subtext="Based on completed interviews"
          color="amber"
        />
        <StatCard
          icon={getTrendIcon(progress?.improvement_trend)}
          label="Trend"
          value={progress?.improvement_trend?.replace("_", " ") || "Start practicing"}
          subtext="Your performance trajectory"
          color="emerald"
          valueClass={getTrendColor(progress?.improvement_trend)}
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-[#111] border border-white/10 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">🚀 Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QuickAction
            icon="📄"
            title="Build Resume"
            description="Create or improve your professional resume"
            color="blue"
          />
          <QuickAction
            icon="❓"
            title="Practice Questions"
            description="Generate interview questions for your target role"
            color="purple"
          />
          <QuickAction
            icon="🎤"
            title="Mock Interview"
            description="Start a realistic practice interview session"
            color="emerald"
          />
        </div>
      </div>

      {/* Recent Sessions */}
      {sessions.length > 0 && (
        <div className="bg-[#111] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📋 Recent Sessions</h3>
          <div className="space-y-3">
            {sessions.slice(0, 5).map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/5"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    session.status === "completed" ? "bg-green-500/20" : "bg-amber-500/20"
                  }`}>
                    <span>{session.status === "completed" ? "✅" : "🔄"}</span>
                  </div>
                  <div>
                    <p className="text-white font-medium">{session.job_title}</p>
                    <p className="text-white/40 text-sm">
                      {session.company || "General"} • {session.interview_type}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {session.overall_score && (
                    <p className="text-white font-semibold">{session.overall_score}/10</p>
                  )}
                  <p className="text-white/40 text-xs">
                    {new Date(session.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tips Section */}
      <div className="bg-[#111] border border-white/10 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">💡 Interview Tips</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TipCard
            title="STAR Method"
            tip="Structure answers as Situation, Task, Action, Result for behavioral questions"
          />
          <TipCard
            title="Research the Company"
            tip="Know the company's mission, recent news, and how you can contribute"
          />
          <TipCard
            title="Prepare Questions"
            tip="Have 3-5 thoughtful questions ready to ask the interviewer"
          />
          <TipCard
            title="Practice Out Loud"
            tip="Rehearse answers verbally to build confidence and fluency"
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, subtext, color, valueClass }: {
  icon: string;
  label: string;
  value: string;
  subtext: string;
  color: string;
  valueClass?: string;
}) {
  const colorMap: Record<string, string> = {
    blue: "bg-blue-500/10 border-blue-500/20",
    purple: "bg-purple-500/10 border-purple-500/20",
    amber: "bg-amber-500/10 border-amber-500/20",
    emerald: "bg-emerald-500/10 border-emerald-500/20",
  };

  return (
    <div className={`${colorMap[color]} border rounded-xl p-4`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{icon}</span>
        <span className="text-white/50 text-sm">{label}</span>
      </div>
      <p className={`text-2xl font-bold capitalize ${valueClass || "text-white"}`}>{value}</p>
      <p className="text-white/40 text-xs mt-1">{subtext}</p>
    </div>
  );
}

function QuickAction({ icon, title, description, color }: {
  icon: string;
  title: string;
  description: string;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    blue: "hover:border-blue-500/50 hover:bg-blue-500/5",
    purple: "hover:border-purple-500/50 hover:bg-purple-500/5",
    emerald: "hover:border-emerald-500/50 hover:bg-emerald-500/5",
  };

  return (
    <button className={`text-left p-4 rounded-xl border border-white/10 transition-all ${colorMap[color]}`}>
      <span className="text-2xl">{icon}</span>
      <h4 className="text-white font-medium mt-2">{title}</h4>
      <p className="text-white/40 text-sm mt-1">{description}</p>
    </button>
  );
}

function TipCard({ title, tip }: { title: string; tip: string }) {
  return (
    <div className="p-4 bg-white/5 rounded-lg">
      <h4 className="text-white font-medium text-sm">{title}</h4>
      <p className="text-white/50 text-sm mt-1">{tip}</p>
    </div>
  );
}
