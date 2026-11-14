import React, { useState, useEffect } from 'react';
import { careerService } from '../../services/careerService';
import { roadmapService } from '../../services/roadmapService';
import { CareerRoleSummary, CareerMatchResponse } from '../../types/career';

interface CareerPathViewProps {
  onNavigateToRoadmap?: () => void;
}

export const CareerPathView: React.FC<CareerPathViewProps> = ({ onNavigateToRoadmap }) => {
  const [roles, setRoles] = useState<CareerRoleSummary[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string>('');
  const [matchData, setMatchData] = useState<CareerMatchResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [matching, setMatching] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [generatingRoadmap, setGeneratingRoadmap] = useState<boolean>(false);

  useEffect(() => {
    loadRolesAndActiveGoal();
  }, []);

  const loadRolesAndActiveGoal = async () => {
    try {
      setLoading(true);
      const roleList = await careerService.listRoles();
      setRoles(roleList);
      if (roleList.length > 0) {
        // Check active goal
        const activeGoal = await careerService.getActiveGoal();
        const initialRoleId = activeGoal ? activeGoal.career_role_id : roleList[0].id;
        setSelectedRoleId(initialRoleId);
        await runMatch(initialRoleId);
      }
    } catch (err: any) {
      console.error('Failed to load career roles:', err);
    } finally {
      setLoading(false);
    }
  };

  const runMatch = async (roleId: string) => {
    try {
      setMatching(true);
      setActionMessage(null);
      const res = await careerService.matchCareer(roleId);
      setMatchData(res);
    } catch (err: any) {
      console.error('Matching failed:', err);
      setActionMessage('Failed to calculate career match. Please confirm your skills first.');
    } finally {
      setMatching(false);
    }
  };

  const handleSelectRole = (roleId: string) => {
    setSelectedRoleId(roleId);
    runMatch(roleId);
  };

  const handleSetTargetGoal = async () => {
    if (!selectedRoleId) return;
    try {
      await careerService.setCareerGoal(selectedRoleId);
      setActionMessage('Target career goal updated successfully!');
    } catch (err: any) {
      setActionMessage('Failed to set career goal.');
    }
  };

  const handleGenerateRoadmap = async () => {
    if (!selectedRoleId) return;
    try {
      setGeneratingRoadmap(true);
      await roadmapService.generateRoadmap(selectedRoleId, false);
      setActionMessage('Personalized learning roadmap generated!');
      if (onNavigateToRoadmap) {
        onNavigateToRoadmap();
      }
    } catch (err: any) {
      setActionMessage('Failed to generate roadmap: ' + (err.message || 'Error'));
    } finally {
      setGeneratingRoadmap(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mr-3"></div>
        Loading career intelligence models...
      </div>
    );
  }

  const selectedRole = roles.find((r) => r.id === selectedRoleId);

  return (
    <div className="max-w-6xl mx-auto space-y-8 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Career Intelligence & Skill Gap Engine</h2>
          <p className="text-slate-400 text-sm mt-1">
            Compare your confirmed learner profile against industry benchmarks to identify readiness and actionable gaps.
          </p>
        </div>
        {matching && (
          <div className="flex items-center gap-2 text-xs text-indigo-400">
            <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-indigo-400"></div>
            Analyzing gap profile...
          </div>
        )}
      </div>

      {actionMessage && (
        <div className="p-4 rounded-xl border bg-indigo-950/40 border-indigo-800/60 text-indigo-200 text-sm flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-indigo-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Role Picker Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {roles.map((role) => {
          const isSelected = role.id === selectedRoleId;
          return (
            <button
              key={role.id}
              onClick={() => handleSelectRole(role.id)}
              className={`p-3 rounded-xl text-left border transition-all text-xs flex flex-col justify-between ${
                isSelected
                  ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-lg shadow-indigo-500/10'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
              }`}
            >
              <div className="font-semibold text-white">{role.title}</div>
              <div className="mt-2 text-[10px] text-slate-400">{role.industry_demand_level} DEMAND</div>
            </button>
          );
        })}
      </div>

      {/* Main Analysis Card */}
      {selectedRole && matchData && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-6">
            <div>
              <div className="flex items-center gap-3">
                <h3 className="text-xl font-bold text-white">{selectedRole.title}</h3>
                <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-indigo-900/50 text-indigo-300 border border-indigo-700/50">
                  {selectedRole.category_name || 'Software Engineering'}
                </span>
                <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-emerald-900/40 text-emerald-300 border border-emerald-700/40">
                  {selectedRole.average_salary_range || '$90,000+'}
                </span>
              </div>
              <p className="text-slate-400 text-sm mt-1">{selectedRole.description}</p>
            </div>

            <div className="flex items-center gap-3 w-full md:w-auto">
              <button
                onClick={handleSetTargetGoal}
                className="flex-1 md:flex-none px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-medium border border-slate-700 transition-colors"
              >
                Set as Target Goal
              </button>
              <button
                onClick={handleGenerateRoadmap}
                disabled={generatingRoadmap}
                className="flex-1 md:flex-none px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2"
              >
                {generatingRoadmap ? 'Generating...' : 'Launch Roadmap →'}
              </button>
            </div>
          </div>

          {/* Readiness Score Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-center gap-4">
              <div className="relative w-16 h-16 flex items-center justify-center">
                <svg className="w-16 h-16 transform -rotate-90">
                  <circle cx="32" cy="32" r="26" stroke="#1e293b" strokeWidth="6" fill="transparent" />
                  <circle
                    cx="32"
                    cy="32"
                    r="26"
                    stroke="#6366f1"
                    strokeWidth="6"
                    fill="transparent"
                    strokeDasharray={163.36}
                    strokeDashoffset={163.36 - (163.36 * matchData.match_percentage) / 100}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute text-sm font-bold text-white">{matchData.match_percentage}%</span>
              </div>
              <div>
                <div className="text-xs text-slate-400 font-medium">Readiness Score</div>
                <div className="text-sm font-bold text-indigo-400">{matchData.gap_summary.readiness_verdict}</div>
              </div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 font-medium">Matching Skills</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">{matchData.matched_skills_count}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">Meets or exceeds requirement</div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 font-medium">Weak Skills</div>
              <div className="text-2xl font-bold text-amber-400 mt-1">{matchData.weak_skills_count}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">Requires proficiency boost</div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 font-medium">Missing Skills</div>
              <div className="text-2xl font-bold text-rose-400 mt-1">{matchData.missing_skills_count}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">Mandatory priority targets</div>
            </div>
          </div>

          {/* AI Gap Diagnosis Banner */}
          <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-900/50">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs tracking-wider uppercase">
              <span>✦</span> AI Gap Analyzer Verdict
            </div>
            <p className="text-indigo-200 text-sm mt-1.5 leading-relaxed">
              {matchData.gap_summary.key_recommendation}
            </p>
          </div>

          {/* Skills Breakdown Grids */}
          <div className="space-y-4">
            {/* Missing Skills */}
            {matchData.missing_skills.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                  Missing Competencies (Priority Gaps)
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  {matchData.missing_skills.map((skill) => (
                    <div key={skill.skill_name} className="p-3 bg-slate-950/40 border border-rose-900/30 rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-white">{skill.skill_name}</div>
                        <div className="text-[11px] text-slate-400">Target Level: {skill.required_proficiency}/4</div>
                      </div>
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-rose-950/80 text-rose-300 border border-rose-800/40">
                        {skill.is_mandatory ? 'MANDATORY' : 'RECOMMENDED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weak Skills */}
            {matchData.weak_skills.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                  Weak / Developing Skills
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  {matchData.weak_skills.map((skill) => (
                    <div key={skill.skill_name} className="p-3 bg-slate-950/40 border border-amber-900/30 rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-white">{skill.skill_name}</div>
                        <div className="text-[11px] text-slate-400">
                          Current: {skill.user_proficiency}/4 → Required: {skill.required_proficiency}/4
                        </div>
                      </div>
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-amber-950/80 text-amber-300 border border-amber-800/40">
                        GAP: +{skill.gap_level}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Matching Skills */}
            {matchData.matching_skills.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  Verified Matching Skills
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  {matchData.matching_skills.map((skill) => (
                    <div key={skill.skill_name} className="p-3 bg-slate-950/40 border border-emerald-900/30 rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-white">{skill.skill_name}</div>
                        <div className="text-[11px] text-emerald-400">Proficiency: Level {skill.user_proficiency}/4</div>
                      </div>
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/40">
                        MATCHED ✓
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
