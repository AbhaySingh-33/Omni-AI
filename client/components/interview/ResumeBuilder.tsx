"use client";
import { useState } from "react";
import { useResume } from "@/hooks/useInterview";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

interface Props {
  token: string;
}

export default function ResumeBuilder({ token }: Props) {
  const { resume, loading, saveResume, generateResume, analyzeResume } = useResume(token);
  const [mode, setMode] = useState<"view" | "edit" | "generate" | "analyze">("view");
  const [resumeContent, setResumeContent] = useState("");
  const [targetJob, setTargetJob] = useState("");
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);

  // Form state for resume generation
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    linkedin: "",
    summary: "",
    skills: "",
    job_title: "",
  });
  const [experiences, setExperiences] = useState([
    { company: "", title: "", startDate: "", endDate: "", description: "" }
  ]);
  const [education, setEducation] = useState([
    { institution: "", degree: "", field: "", graduationDate: "" }
  ]);

  const handleSave = async () => {
    await saveResume(resumeContent, targetJob);
    setMode("view");
  };

  const handleGenerate = async () => {
    setGenerating(true);
    const result = await generateResume({
      name: formData.name,
      email: formData.email,
      phone: formData.phone || undefined,
      linkedin: formData.linkedin || undefined,
      summary: formData.summary || undefined,
      experience: experiences.filter(e => e.company && e.title),
      education: education.filter(e => e.institution && e.degree),
      skills: formData.skills.split(",").map(s => s.trim()).filter(Boolean),
      job_title: formData.job_title || undefined,
    });
    if (result?.content) {
      setResumeContent(result.content);
      setMode("edit");
    }
    setGenerating(false);
  };

  const handleAnalyze = async () => {
    const content = resumeContent || resume?.content;
    if (!content) return;

    setGenerating(true);
    const result = await analyzeResume(content, targetJob);
    if (result?.analysis) {
      setAnalysis(result.analysis);
      setMode("analyze");
    }
    setGenerating(false);
  };

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const response = await fetch(`${AI_ENGINE_URL}/interview/resume/pdf`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        alert(error.detail || "Failed to download PDF");
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "resume.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("PDF download error:", error);
      alert("Failed to download PDF");
    } finally {
      setDownloading(false);
    }
  };

  const addExperience = () => {
    setExperiences([...experiences, { company: "", title: "", startDate: "", endDate: "", description: "" }]);
  };

  const addEducation = () => {
    setEducation([...education, { institution: "", degree: "", field: "", graduationDate: "" }]);
  };

  if (loading && !resume) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">📄 Resume Builder</h2>
          <p className="text-white/50 text-sm">Create, edit, and optimize your professional resume</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMode("generate")}
            className="px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg text-sm font-medium hover:bg-purple-500/30 transition-colors"
          >
            ✨ Generate New
          </button>
          {(resume?.content || resumeContent) && (
            <>
              <button
                onClick={handleAnalyze}
                disabled={generating}
                className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg text-sm font-medium hover:bg-blue-500/30 transition-colors disabled:opacity-50"
              >
                {generating ? "Analyzing..." : "🔍 Analyze"}
              </button>
              <button
                onClick={handleDownloadPDF}
                disabled={downloading}
                className="px-4 py-2 bg-green-500/20 text-green-400 rounded-lg text-sm font-medium hover:bg-green-500/30 transition-colors disabled:opacity-50"
              >
                {downloading ? "Downloading..." : "📥 Download PDF"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Mode: View */}
      {mode === "view" && (
        <div className="bg-[#111] border border-white/10 rounded-xl p-6">
          {resume?.content ? (
            <>
              <div className="flex justify-between items-start mb-4">
                <p className="text-white/40 text-sm">
                  Last updated: {new Date(resume.updated_at).toLocaleDateString()}
                </p>
                <button
                  onClick={() => {
                    setResumeContent(resume.content);
                    setMode("edit");
                  }}
                  className="text-sm text-purple-400 hover:text-purple-300"
                >
                  ✏️ Edit
                </button>
              </div>
              <div className="prose prose-invert max-w-none">
                <pre className="whitespace-pre-wrap text-white/80 font-sans text-sm leading-relaxed">
                  {resume.content}
                </pre>
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <span className="text-4xl mb-4 block">📄</span>
              <h3 className="text-white font-medium mb-2">No Resume Yet</h3>
              <p className="text-white/50 text-sm mb-4">
                Create your professional resume to get started with interview prep
              </p>
              <button
                onClick={() => setMode("generate")}
                className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm font-medium hover:bg-purple-600 transition-colors"
              >
                Create Resume
              </button>
            </div>
          )}
        </div>
      )}

      {/* Mode: Edit */}
      {mode === "edit" && (
        <div className="bg-[#111] border border-white/10 rounded-xl p-6 space-y-4">
          <div>
            <label className="block text-white/60 text-sm mb-2">Target Job Title (optional)</label>
            <input
              type="text"
              value={targetJob}
              onChange={(e) => setTargetJob(e.target.value)}
              placeholder="e.g., Software Engineer, Product Manager"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder:text-white/30"
            />
          </div>
          <div>
            <label className="block text-white/60 text-sm mb-2">Resume Content</label>
            <textarea
              value={resumeContent}
              onChange={(e) => setResumeContent(e.target.value)}
              rows={20}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-mono text-sm resize-none"
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={loading}
              className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 transition-colors disabled:opacity-50"
            >
              {loading ? "Saving..." : "💾 Save Resume"}
            </button>
            <button
              onClick={() => setMode("view")}
              className="px-4 py-2 bg-white/10 text-white rounded-lg text-sm font-medium hover:bg-white/20 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Mode: Generate */}
      {mode === "generate" && (
        <div className="bg-[#111] border border-white/10 rounded-xl p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white/60 text-sm mb-2">Full Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-white/60 text-sm mb-2">Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-white/60 text-sm mb-2">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-white/60 text-sm mb-2">LinkedIn URL</label>
              <input
                type="url"
                value={formData.linkedin}
                onChange={(e) => setFormData({ ...formData, linkedin: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-white/60 text-sm mb-2">Target Job Title</label>
            <input
              type="text"
              value={formData.job_title}
              onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
              placeholder="e.g., Senior Frontend Developer"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-white/60 text-sm mb-2">Professional Summary</label>
            <textarea
              value={formData.summary}
              onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
              rows={3}
              placeholder="Brief overview of your professional background and goals..."
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white resize-none"
            />
          </div>

          {/* Experience */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <label className="text-white/60 text-sm">Work Experience</label>
              <button onClick={addExperience} className="text-purple-400 text-sm hover:text-purple-300">
                + Add Experience
              </button>
            </div>
            {experiences.map((exp, idx) => (
              <div key={idx} className="bg-white/5 rounded-lg p-4 mb-3 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input
                    placeholder="Company"
                    value={exp.company}
                    onChange={(e) => {
                      const updated = [...experiences];
                      updated[idx].company = e.target.value;
                      setExperiences(updated);
                    }}
                    className="bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm"
                  />
                  <input
                    placeholder="Job Title"
                    value={exp.title}
                    onChange={(e) => {
                      const updated = [...experiences];
                      updated[idx].title = e.target.value;
                      setExperiences(updated);
                    }}
                    className="bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm"
                  />
                  <input
                    placeholder="Start Date (e.g., Jan 2020)"
                    value={exp.startDate}
                    onChange={(e) => {
                      const updated = [...experiences];
                      updated[idx].startDate = e.target.value;
                      setExperiences(updated);
                    }}
                    className="bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm"
                  />
                  <input
                    placeholder="End Date (or Present)"
                    value={exp.endDate}
                    onChange={(e) => {
                      const updated = [...experiences];
                      updated[idx].endDate = e.target.value;
                      setExperiences(updated);
                    }}
                    className="bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm"
                  />
                </div>
                <textarea
                  placeholder="Key responsibilities and achievements..."
                  value={exp.description}
                  onChange={(e) => {
                    const updated = [...experiences];
                    updated[idx].description = e.target.value;
                    setExperiences(updated);
                  }}
                  rows={2}
                  className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm resize-none"
                />
              </div>
            ))}
          </div>

          {/* Education */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <label className="text-white/60 text-sm">Education</label>
              <button onClick={addEducation} className="text-purple-400 text-sm hover:text-purple-300">
                + Add Education
              </button>
            </div>
            {education.map((edu, idx) => (
              <div key={idx} className="bg-white/5 rounded-lg p-4 mb-3 grid grid-cols-2 gap-3">
                <input
                  placeholder="Institution"
                  value={edu.institution}
                  onChange={(e) => {
                    const updated = [...education];
                    updated[idx].institution = e.target.value;
                    setEducation(updated);
                  }}
                  className="bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm"
                />
                <input
                  placeholder="Degree"
                  value={edu.degree}
                  onChange={(e) => {
                    const updated = [...education];
                    updated[idx].degree = e.target.value;
                    setEducation(updated);
                  }}
                  className="bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm"
                />
                <input
                  placeholder="Field of Study"
                  value={edu.field}
                  onChange={(e) => {
                    const updated = [...education];
                    updated[idx].field = e.target.value;
                    setEducation(updated);
                  }}
                  className="bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm"
                />
                <input
                  placeholder="Graduation Date"
                  value={edu.graduationDate}
                  onChange={(e) => {
                    const updated = [...education];
                    updated[idx].graduationDate = e.target.value;
                    setEducation(updated);
                  }}
                  className="bg-white/5 border border-white/10 rounded px-3 py-2 text-white text-sm"
                />
              </div>
            ))}
          </div>

          {/* Skills */}
          <div>
            <label className="block text-white/60 text-sm mb-2">Skills (comma-separated)</label>
            <input
              type="text"
              value={formData.skills}
              onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
              placeholder="JavaScript, React, Node.js, Python, SQL..."
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white"
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleGenerate}
              disabled={generating || !formData.name || !formData.email}
              className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm font-medium hover:bg-purple-600 transition-colors disabled:opacity-50"
            >
              {generating ? "Generating..." : "✨ Generate Resume"}
            </button>
            <button
              onClick={() => setMode("view")}
              className="px-4 py-2 bg-white/10 text-white rounded-lg text-sm font-medium hover:bg-white/20 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Mode: Analyze */}
      {mode === "analyze" && analysis && (
        <div className="bg-[#111] border border-white/10 rounded-xl p-6 space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-white">📊 Resume Analysis</h3>
            <button
              onClick={() => setMode("view")}
              className="text-white/50 hover:text-white text-sm"
            >
              ← Back to Resume
            </button>
          </div>

          {/* Scores */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-blue-400">
                {(analysis.overall_score as number) || "N/A"}/10
              </p>
              <p className="text-white/50 text-sm">Overall Score</p>
            </div>
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-purple-400">
                {(analysis.ats_score as number) || "N/A"}/10
              </p>
              <p className="text-white/50 text-sm">ATS Score</p>
            </div>
          </div>

          {/* Strengths */}
          {Array.isArray(analysis.strengths) && analysis.strengths.length > 0 && (
            <div>
              <h4 className="text-white font-medium mb-2">✅ Strengths</h4>
              <ul className="space-y-2">
                {(analysis.strengths as string[]).map((s, i) => (
                  <li key={i} className="text-white/70 text-sm flex items-start gap-2">
                    <span className="text-green-400">•</span> {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Improvements */}
          {Array.isArray(analysis.improvements) && analysis.improvements.length > 0 && (
            <div>
              <h4 className="text-white font-medium mb-2">📝 Areas for Improvement</h4>
              <ul className="space-y-2">
                {(analysis.improvements as string[]).map((s, i) => (
                  <li key={i} className="text-white/70 text-sm flex items-start gap-2">
                    <span className="text-amber-400">•</span> {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Quick Wins */}
          {Array.isArray(analysis.quick_wins) && analysis.quick_wins.length > 0 && (
            <div>
              <h4 className="text-white font-medium mb-2">⚡ Quick Wins</h4>
              <ul className="space-y-2">
                {(analysis.quick_wins as string[]).map((s, i) => (
                  <li key={i} className="text-white/70 text-sm flex items-start gap-2">
                    <span className="text-purple-400">•</span> {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Raw feedback fallback */}
          {analysis.raw_feedback && (
            <div className="bg-white/5 rounded-lg p-4">
              <pre className="whitespace-pre-wrap text-white/70 text-sm">
                {analysis.raw_feedback as string}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
