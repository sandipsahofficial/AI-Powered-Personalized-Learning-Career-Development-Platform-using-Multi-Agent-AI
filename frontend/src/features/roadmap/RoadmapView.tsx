import React, { useState, useEffect } from 'react';
import { roadmapService } from '../../services/roadmapService';
import { LearningRoadmapResponse, MilestoneResponse } from '../../types/roadmap';

interface RoadmapViewProps {
  onStartAssessment?: (milestoneId: string, milestoneTitle: string) => void;
  onNavigateToCareers?: () => void;
}

export const RoadmapView: React.FC<RoadmapViewProps> = ({ onStartAssessment, onNavigateToCareers }) => {
  const [roadmap, setRoadmap] = useState<LearningRoadmapResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    loadActiveRoadmap();
  }, []);

  const loadActiveRoadmap = async () => {
    try {
      setLoading(true);
      const res = await roadmapService.getActiveRoadmap();
      setRoadmap(res);
    } catch (err: any) {
      console.error('Failed to load roadmap:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (
    milestoneId: string,
    newStatus: 'LOCKED' | 'IN_PROGRESS' | 'REVIEW_PENDING' | 'COMPLETED' | 'REMEDIAL'
  ) => {
    try {
      setUpdatingId(milestoneId);
      const updated = await roadmapService.updateMilestoneStatus(milestoneId, newStatus);
      setRoadmap(updated);
      setNotice(`Milestone status updated to ${newStatus}.`);
    } catch (err: any) {
      setNotice('Failed to update milestone status.');
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mr-3"></div>
        Loading personalized roadmap pathway...
      </div>
    );
  }

  if (!roadmap) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center bg-slate-900 border border-slate-800 rounded-2xl my-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center text-indigo-400 text-2xl font-bold">
          ✦
        </div>
        <h3 className="text-xl font-bold text-white mb-2">No Active Learning Roadmap Found</h3>
        <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
          Select a career goal to generate a customized curriculum mapped to your exact skill gaps.
        </p>
        <button
          onClick={onNavigateToCareers}
          className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/20 transition-all"
        >
          Select Career Goal & Generate Roadmap →
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 p-6">
      {/* Header and Progress Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Active Career Pathway</span>
            <h2 className="text-2xl font-bold text-white mt-0.5">{roadmap.title}</h2>
            <p className="text-slate-400 text-xs mt-1">
              Target Role: <span className="text-slate-200 font-medium">{roadmap.career_role_title}</span> • Est. Duration: <span className="text-slate-200 font-medium">{roadmap.total_estimated_hours} Hours</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => handleUpdateStatus(roadmap.milestones[0].id, 'IN_PROGRESS')}
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              Sync
            </button>
            <span className="px-3 py-1 bg-indigo-950 text-indigo-300 border border-indigo-800/50 rounded-full text-xs font-semibold">
              {roadmap.progress_percentage}% COMPLETED
            </span>
          </div>
        </div>

        {/* Linear Progress Bar */}
        <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-3 rounded-full transition-all duration-500"
            style={{ width: `${roadmap.progress_percentage}%` }}
          ></div>
        </div>
      </div>

      {notice && (
        <div className="p-4 rounded-xl border bg-slate-900 border-indigo-800/40 text-indigo-300 text-sm flex items-center justify-between">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Sequential Milestones */}
      <div className="space-y-6">
        {roadmap.milestones.map((ms: MilestoneResponse, index: number) => {
          const isLocked = ms.status === 'LOCKED';
          const isInProgress = ms.status === 'IN_PROGRESS';
          const isCompleted = ms.status === 'COMPLETED';
          const isRemedial = ms.status === 'REMEDIAL';

          return (
            <div
              key={ms.id}
              className={`rounded-2xl border transition-all p-6 ${
                isCompleted
                  ? 'bg-slate-900/40 border-emerald-900/40'
                  : isRemedial
                  ? 'bg-rose-950/20 border-rose-800/60 shadow-lg shadow-rose-950/20'
                  : isInProgress
                  ? 'bg-slate-900 border-indigo-500/60 shadow-lg shadow-indigo-950/20 ring-1 ring-indigo-500/20'
                  : 'bg-slate-950/40 border-slate-800/60 opacity-60'
              }`}
            >
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm ${
                      isCompleted
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : isRemedial
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : isInProgress
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {isCompleted ? '✓' : index + 1}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">{ms.title}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">Estimated Commitment: ~{ms.estimated_hours} Hours</p>
                  </div>
                </div>

                {/* Status Badges */}
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
                      isCompleted
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-800/50'
                        : isRemedial
                        ? 'bg-rose-950 text-rose-300 border-rose-800 animate-pulse'
                        : isInProgress
                        ? 'bg-indigo-950 text-indigo-300 border-indigo-700/60'
                        : 'bg-slate-900 text-slate-400 border-slate-800'
                    }`}
                  >
                    {ms.status}
                  </span>
                </div>
              </div>

              {/* Remedial Alert Notice */}
              {isRemedial && (
                <div className="mt-4 p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/50 text-xs text-rose-200 space-y-1">
                  <div className="font-semibold flex items-center gap-1.5 text-rose-300">
                    <span>⚠</span> Adaptive Replanner Action: Remedial Attention Required
                  </div>
                  <div>
                    Your recent assessment score fell below the 70% proficiency threshold.
                    Review the curated materials below before re-attempting the competency quiz.
                  </div>
                </div>
              )}

              {/* Milestone Details */}
              <div className="mt-4 space-y-3">
                <p className="text-sm text-slate-300 leading-relaxed">{ms.description}</p>

                {ms.deliverable_title && (
                  <div className="p-3 bg-slate-950/50 border border-slate-800/70 rounded-xl">
                    <div className="text-xs font-semibold text-indigo-400 flex items-center gap-1.5">
                      <span>✦</span> Milestone Deliverable: {ms.deliverable_title}
                    </div>
                    {ms.deliverable_criteria && (
                      <p className="text-xs text-slate-400 mt-1 leading-normal">{ms.deliverable_criteria}</p>
                    )}
                  </div>
                )}
              </div>

              {/* Curated Resources Section */}
              {ms.resources.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-800/60">
                  <div className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                    Curated Free Learning Resources
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                    {ms.resources.map((res) => (
                      <a
                        key={res.id}
                        href={res.url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-3 bg-slate-950/40 border border-slate-800 hover:border-slate-700 rounded-xl transition-colors block text-xs group"
                      >
                        <div className="font-medium text-slate-200 group-hover:text-indigo-400 transition-colors line-clamp-1">
                          {res.title} ↗
                        </div>
                        <div className="flex items-center gap-2 mt-1.5 text-[10px] text-slate-500">
                          <span>{res.provider_name || 'Free Reference'}</span>
                          <span>•</span>
                          <span className="text-emerald-400 font-medium">★ {res.rating}</span>
                          <span>•</span>
                          <span>{res.estimated_minutes}m</span>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="mt-5 pt-4 border-t border-slate-800/60 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  {!isLocked && (
                    <button
                      onClick={() => handleUpdateStatus(ms.id, isCompleted ? 'IN_PROGRESS' : 'COMPLETED')}
                      disabled={updatingId === ms.id}
                      className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
                    >
                      {isCompleted ? 'Mark as In Progress' : 'Mark as Completed ✓'}
                    </button>
                  )}
                </div>

                {!isLocked && onStartAssessment && (
                  <button
                    onClick={() => onStartAssessment(ms.id, ms.title)}
                    className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-md ${
                      isRemedial
                        ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/20'
                        : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20'
                    }`}
                  >
                    {isRemedial ? 'Retake Competency Quiz ↺' : 'Take Competency Assessment →'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
