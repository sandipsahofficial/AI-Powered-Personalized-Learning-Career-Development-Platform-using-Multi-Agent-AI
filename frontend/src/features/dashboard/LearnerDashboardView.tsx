import React, { useState, useEffect } from 'react';
import { assessmentService } from '../../services/assessmentService';
import { roadmapService } from '../../services/roadmapService';
import { ProgressSummaryResponse } from '../../types/assessment';
import { CuratedResourceItem } from '../../types/roadmap';

interface LearnerDashboardViewProps {
  onNavigateTab: (tabId: string) => void;
}

export const LearnerDashboardView: React.FC<LearnerDashboardViewProps> = ({ onNavigateTab }) => {
  const [summary, setSummary] = useState<ProgressSummaryResponse | null>(null);
  const [resources, setResources] = useState<CuratedResourceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [sumData, resData] = await Promise.all([
        assessmentService.getProgressSummary(),
        roadmapService.getRecommendedResources(),
      ]);
      setSummary(sumData);
      setResources(resData);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20 text-slate-400 text-sm">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mr-3"></div>
        Aggregating learner progress and competency metrics...
      </div>
    );
  }

  const roleTitle = summary?.target_career_title || 'Full Stack Developer';
  const readiness = summary?.readiness_percentage || 0;
  const roadmapPct = summary?.roadmap_progress_percentage || 0;

  return (
    <div className="max-w-6xl mx-auto space-y-8 p-6">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900/60 via-slate-900 to-slate-900 border border-indigo-800/40 p-8">
        <div className="relative z-10 max-w-2xl">
          <span className="px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold">
            ✦ AI-Powered Adaptive Learning Platform
          </span>
          <h1 className="text-3xl font-extrabold text-white tracking-tight mt-3">
            Welcome to Your Career Acceleration Portal
          </h1>
          <p className="text-slate-300 text-sm mt-2 leading-relaxed">
            Your personalized development environment driven by collaborative multi-agent AI:
            Skill Profiling, Career Intelligence, Dynamic Roadmaps, and Contextual Mentorship.
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-6">
            <button
              onClick={() => onNavigateTab('profiling')}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all"
            >
              Update Skill Profile →
            </button>
            <button
              onClick={() => onNavigateTab('careers')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-medium transition-all"
            >
              Analyze Career Gaps
            </button>
            <button
              onClick={() => onNavigateTab('mentor')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-indigo-800/50 rounded-xl text-xs font-medium transition-all"
            >
              Chat with AI Mentor ✦
            </button>
          </div>
        </div>
      </div>

      {/* 4 Primary Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Career Match */}
        <div
          onClick={() => onNavigateTab('careers')}
          className="bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-5 cursor-pointer transition-all group"
        >
          <div className="flex justify-between items-start">
            <div className="text-xs font-semibold text-slate-400">Target Career</div>
            <span className="text-xs text-indigo-400 group-hover:translate-x-0.5 transition-transform">→</span>
          </div>
          <div className="text-base font-bold text-white mt-1 line-clamp-1">{roleTitle}</div>
          <div className="mt-4 flex items-center justify-between text-xs">
            <span className="text-slate-400">Readiness Score</span>
            <span className="text-emerald-400 font-bold text-sm">{readiness}%</span>
          </div>
          <div className="w-full bg-slate-950 rounded-full h-1.5 mt-2">
            <div className="bg-emerald-400 h-1.5 rounded-full" style={{ width: `${readiness}%` }}></div>
          </div>
        </div>

        {/* Roadmap Progress */}
        <div
          onClick={() => onNavigateTab('roadmap')}
          className="bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-5 cursor-pointer transition-all group"
        >
          <div className="flex justify-between items-start">
            <div className="text-xs font-semibold text-slate-400">Roadmap Progress</div>
            <span className="text-xs text-indigo-400 group-hover:translate-x-0.5 transition-transform">→</span>
          </div>
          <div className="text-2xl font-bold text-white mt-1">{roadmapPct}%</div>
          <div className="mt-4 flex items-center justify-between text-xs">
            <span className="text-slate-400">Milestones Done</span>
            <span className="text-indigo-300 font-bold">
              {summary?.completed_milestones_count || 0} / {summary?.total_milestones_count || 4}
            </span>
          </div>
          <div className="w-full bg-slate-950 rounded-full h-1.5 mt-2">
            <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${roadmapPct}%` }}></div>
          </div>
        </div>

        {/* Confirmed Skills */}
        <div
          onClick={() => onNavigateTab('profiling')}
          className="bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-5 cursor-pointer transition-all group"
        >
          <div className="flex justify-between items-start">
            <div className="text-xs font-semibold text-slate-400">Confirmed Skills</div>
            <span className="text-xs text-indigo-400 group-hover:translate-x-0.5 transition-transform">→</span>
          </div>
          <div className="text-2xl font-bold text-white mt-1">{summary?.confirmed_skills_count || 0}</div>
          <div className="mt-4 text-xs text-slate-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Evidence-based profile</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-2">Click to review & add skills</div>
        </div>

        {/* Competency Assessments */}
        <div
          onClick={() => onNavigateTab('roadmap')}
          className="bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-5 cursor-pointer transition-all group"
        >
          <div className="flex justify-between items-start">
            <div className="text-xs font-semibold text-slate-400">Assessments Taken</div>
            <span className="text-xs text-indigo-400 group-hover:translate-x-0.5 transition-transform">→</span>
          </div>
          <div className="text-2xl font-bold text-white mt-1">{summary?.assessments_taken_count || 0}</div>
          <div className="mt-4 flex items-center justify-between text-xs">
            <span className="text-slate-400">Passed Threshold</span>
            <span className="text-emerald-400 font-bold">{summary?.assessments_passed_count || 0} Passed</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-2">Adaptive replanner enabled</div>
        </div>
      </div>

      {/* Recommended Learning Resources */}
      {resources.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Curated Free Learning Resources</h3>
              <p className="text-slate-400 text-xs mt-0.5">
                Authoritative documentation and tutorials prioritized for your missing skills
              </p>
            </div>
            <button
              onClick={() => onNavigateTab('roadmap')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              View Full Roadmap →
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {resources.slice(0, 6).map((res) => (
              <a
                key={res.id}
                href={res.url}
                target="_blank"
                rel="noreferrer"
                className="p-3.5 bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-xl transition-colors block text-xs group"
              >
                <div className="font-semibold text-slate-200 group-hover:text-indigo-400 transition-colors line-clamp-1">
                  {res.title} ↗
                </div>
                <p className="text-slate-400 text-[11px] mt-1 line-clamp-2 leading-relaxed">
                  {res.content_summary}
                </p>
                <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-800/80 text-[10px] text-slate-500">
                  <span className="text-indigo-400 font-medium">{res.provider_name || 'Documentation'}</span>
                  <span>•</span>
                  <span className="text-emerald-400">★ {res.rating}</span>
                  <span>•</span>
                  <span>~{res.estimated_minutes}m</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
