import React, { useState, useEffect } from 'react';
import { profilingService } from '../../services/profilingService';
import {
  ProfilePreviewResponse,
  ExtractedSkillItem,
  ProfilingStatusResponse
} from '../../types/profiling';

export const LearnerProfilingView: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [textInput, setTextInput] = useState('');
  const [activeTab, setActiveTab] = useState<'upload' | 'text'>('upload');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processStep, setProcessStep] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<ProfilePreviewResponse | null>(null);
  const [status, setStatus] = useState<ProfilingStatusResponse | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New manual skill form
  const [showAddModal, setShowAddModal] = useState(false);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('Programming Languages');
  const [newSkillLevel, setNewSkillLevel] = useState<number>(3);

  useEffect(() => {
    loadStatus();
    loadPreview();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await profilingService.getStatus();
      setStatus(data);
    } catch {
      // Ignore initial load failure
    }
  };

  const loadPreview = async () => {
    try {
      const data = await profilingService.getPreview();
      setPreview(data);
    } catch {
      // No preview yet
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUploadAndExtract = async () => {
    setError(null);
    setSuccessMsg(null);
    setIsProcessing(true);

    try {
      if (activeTab === 'upload') {
        if (!file) {
          setError('Please select a resume file (.pdf, .docx, or .txt).');
          setIsProcessing(false);
          return;
        }
        setProcessStep('1/2 Parsing and sanitizing document...');
        await profilingService.uploadResume(file);
        
        setProcessStep('2/2 AI Profiler Agent extracting skills & evaluating evidence...');
        const previewData = await profilingService.extractSkills(undefined, true);
        setPreview(previewData);
      } else {
        if (!textInput.trim()) {
          setError('Please paste your profile text or project descriptions.');
          setIsProcessing(false);
          return;
        }
        setProcessStep('AI Profiler Agent analyzing raw profile text...');
        const previewData = await profilingService.extractSkills(textInput, false);
        setPreview(previewData);
      }

      await loadStatus();
      setSuccessMsg('Skill extraction complete! Please review and confirm your skills below.');
    } catch (err: any) {
      setError(err.message || 'Profiling extraction failed. Please try again.');
    } finally {
      setIsProcessing(false);
      setProcessStep('');
    }
  };

  const handleUpdateProficiency = async (skillId: string, level: number) => {
    try {
      const updated = await profilingService.updateSkill(skillId, {
        proficiency_level: level,
        is_confirmed: true,
        is_rejected: false,
      });

      if (preview) {
        setPreview({
          ...preview,
          extracted_skills: preview.extracted_skills.map((s) => (s.id === skillId ? updated : s)),
        });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update proficiency');
    }
  };

  const handleToggleAccept = async (skill: ExtractedSkillItem) => {
    const nextConfirmed = !skill.is_confirmed;
    try {
      const updated = await profilingService.updateSkill(skill.id, {
        is_confirmed: nextConfirmed,
        is_rejected: false,
      });
      if (preview) {
        setPreview({
          ...preview,
          extracted_skills: preview.extracted_skills.map((s) => (s.id === skill.id ? updated : s)),
        });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update skill confirmation');
    }
  };

  const handleToggleReject = async (skill: ExtractedSkillItem) => {
    const nextRejected = !skill.is_rejected;
    try {
      const updated = await profilingService.updateSkill(skill.id, {
        is_rejected: nextRejected,
        is_confirmed: false,
      });
      if (preview) {
        setPreview({
          ...preview,
          extracted_skills: preview.extracted_skills.map((s) => (s.id === skill.id ? updated : s)),
        });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update rejection');
    }
  };

  const handleAddManualSkill = () => {
    if (!newSkillName.trim()) return;

    const manualSkill: ExtractedSkillItem = {
      id: `manual_${Date.now()}`,
      canonical_name: newSkillName.trim(),
      category: newSkillCategory,
      original_phrase: newSkillName.trim(),
      proficiency_level: newSkillLevel,
      proficiency_status: 'USER_CONFIRMED',
      confidence_score: 1.0,
      evidence: [
        {
          evidence_type: 'EXPLICITLY_DECLARED',
          source_section: 'Manual Entry',
          original_phrase: newSkillName.trim(),
          description: 'Manually added by learner during profile review.',
          confidence_score: 1.0,
        },
      ],
      normalization_method: 'MANUAL_ENTRY',
      is_confirmed: true,
      is_rejected: false,
      user_notes: 'User self-reported skill',
    };

    if (preview) {
      setPreview({
        ...preview,
        extracted_skills: [manualSkill, ...preview.extracted_skills],
        total_skills_count: preview.total_skills_count + 1,
      });
    }

    setNewSkillName('');
    setShowAddModal(false);
  };

  const handleConfirmAll = async () => {
    if (!preview || preview.extracted_skills.length === 0) return;
    setIsProcessing(true);
    setError(null);

    try {
      const confirmedIds = preview.extracted_skills
        .filter((s) => !s.is_rejected)
        .map((s) => s.id);

      const res = await profilingService.confirmProfile(confirmedIds);
      setSuccessMsg(res.message);
      await loadStatus();
    } catch (err: any) {
      setError(err.message || 'Failed to persist confirmed profile.');
    } finally {
      setIsProcessing(false);
    }
  };

  const getEvidenceBadge = (type: string) => {
    switch (type) {
      case 'PROJECT_DEMONSTRATED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Project Verified</span>;
      case 'CERTIFICATION_SUPPORTED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">Certified</span>;
      case 'EXPERIENCE_INFERRED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Experience Inferred</span>;
      case 'INSUFFICIENT_EVIDENCE':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">Weak Evidence</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">Declared</span>;
    }
  };

  const getLevelLabel = (lvl: number | null) => {
    switch (lvl) {
      case 5: return 'Level 5 (Expert)';
      case 4: return 'Level 4 (Advanced)';
      case 3: return 'Level 3 (Intermediate)';
      case 2: return 'Level 2 (Basic)';
      case 1: return 'Level 1 (Beginner)';
      default: return 'Needs Review';
    }
  };

  return (
    <div className="w-full max-w-5xl space-y-6">
      {/* Header Banner */}
      <div className="p-6 sm:p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🔍</span>
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              AI Profiling & Skill Extraction Engine
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Upload your resume or paste experience details. The AI Profiler Agent extracts, normalizes,
            and validates evidence-backed skills against canonical industry benchmarks.
          </p>
        </div>

        {status && (
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="px-4 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-center">
              <span className="text-[10px] uppercase font-mono text-slate-500 block">Persisted Skills</span>
              <span className="text-lg font-bold text-emerald-400">{status.total_persisted_skills}</span>
            </div>
            <div className="px-4 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-center">
              <span className="text-[10px] uppercase font-mono text-slate-500 block">Awaiting Review</span>
              <span className="text-lg font-bold text-sky-400">
                {preview ? preview.extracted_skills.filter((s) => !s.is_confirmed && !s.is_rejected).length : 0}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Alert Notices */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
          <span>✅</span>
          <span>{successMsg}</span>
        </div>
      )}

      {/* Section A: Ingestion Form */}
      <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-lg">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('upload')}
              className={`text-xs px-3.5 py-1.5 rounded-lg font-medium transition-colors ${
                activeTab === 'upload'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              📄 Upload Resume Document
            </button>
            <button
              onClick={() => setActiveTab('text')}
              className={`text-xs px-3.5 py-1.5 rounded-lg font-medium transition-colors ${
                activeTab === 'text'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ✍️ Paste Raw Text
            </button>
          </div>
          <span className="text-[11px] text-slate-500">Supports PDF, DOCX, TXT up to 5MB</span>
        </div>

        {activeTab === 'upload' ? (
          <div className="space-y-4">
            <div className="border-2 border-dashed border-slate-800 hover:border-sky-500/40 rounded-xl p-8 text-center transition-colors">
              <input
                type="file"
                id="resume-upload"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
              <label htmlFor="resume-upload" className="cursor-pointer flex flex-col items-center">
                <span className="text-3xl mb-2">📁</span>
                <span className="text-sm font-semibold text-slate-200">
                  {file ? file.name : 'Click to select or drag and drop your resume file'}
                </span>
                <span className="text-xs text-slate-500 mt-1">PDF, Word (DOCX), or plain text format</span>
              </label>
            </div>
          </div>
        ) : (
          <div>
            <textarea
              rows={5}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Paste your technical skills, projects, certifications, or work experience summary here..."
              className="w-full p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500/40 text-sm"
            />
          </div>
        )}

        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={handleUploadAndExtract}
            disabled={isProcessing}
            className="px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isProcessing ? (
              <>
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                <span>{processStep || 'Processing with Ollama...'}</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>Analyze & Extract Skills</span>
              </>
            )}
          </button>

          {preview && (
            <button
              onClick={() => setShowAddModal(true)}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            >
              + Add Missing Skill
            </button>
          )}
        </div>
      </div>

      {/* Section B & C: Extraction Preview & Interactive Skill Review */}
      {preview && (
        <div className="space-y-6">
          {/* Document Summary Card */}
          {preview.document_summary && (
            <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-mono text-sky-400 uppercase tracking-wider block">Candidate Overview</span>
                <h3 className="text-base font-bold text-white mt-0.5">{preview.document_summary.headline}</h3>
                <p className="text-xs text-slate-400 mt-1">{preview.document_summary.summary}</p>
              </div>
              <div className="flex items-center gap-2 self-start sm:self-auto">
                <span className="text-xs px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                  Model: {preview.ai_model_used}
                </span>
                {preview.is_fallback && (
                  <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono">
                    Deterministic Fallback
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Category Breakdown Badges */}
          <div className="flex flex-wrap gap-2">
            {Object.entries(preview.categories_breakdown).map(([cat, count]) => (
              <span key={cat} className="px-3 py-1 rounded-full text-xs bg-slate-900 border border-slate-800 text-slate-300 flex items-center gap-2">
                <span>{cat}</span>
                <span className="w-5 h-5 rounded-full bg-slate-800 text-sky-400 font-bold text-[10px] flex items-center justify-center">
                  {count}
                </span>
              </span>
            ))}
          </div>

          {/* Skill Review List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                <span>Identified Skills & Evidence</span>
                <span className="text-xs font-normal text-slate-400">({preview.extracted_skills.length} skills)</span>
              </h2>

              <button
                onClick={handleConfirmAll}
                disabled={isProcessing}
                className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-1.5"
              >
                <span>💾</span>
                <span>Confirm & Save to Profile</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {preview.extracted_skills.map((skill) => (
                <div
                  key={skill.id}
                  className={`p-4 rounded-xl border transition-all ${
                    skill.is_rejected
                      ? 'bg-slate-950/40 border-slate-800/40 opacity-50'
                      : skill.is_confirmed
                      ? 'bg-slate-900 border-emerald-500/30 shadow-md shadow-emerald-500/5'
                      : 'bg-slate-900 border-slate-800'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white">{skill.canonical_name}</span>
                        {getEvidenceBadge(skill.evidence[0]?.evidence_type || 'EXPLICITLY_DECLARED')}
                      </div>
                      <span className="text-[11px] text-slate-500 block mt-0.5">
                        Category: {skill.category} &bull; Matched via {skill.normalization_method}
                      </span>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleToggleAccept(skill)}
                        title="Accept / Confirm"
                        className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold transition-colors ${
                          skill.is_confirmed ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                        }`}
                      >
                        ✓
                      </button>
                      <button
                        onClick={() => handleToggleReject(skill)}
                        title="Reject / Discard"
                        className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold transition-colors ${
                          skill.is_rejected ? 'bg-rose-500 text-slate-950' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                        }`}
                      >
                        ✕
                      </button>
                    </div>
                  </div>

                  {/* Evidence snippets */}
                  <div className="mt-2.5 p-2 rounded-lg bg-slate-950/70 border border-slate-800/60 text-xs text-slate-400">
                    <span className="font-semibold text-slate-300">Context: </span>
                    {skill.evidence[0]?.description || 'Identified from candidate profile details.'}
                  </div>

                  {/* Proficiency Slider / Selector */}
                  <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-800/80">
                    <span className="text-[11px] text-slate-400">
                      Proficiency: <strong className="text-sky-400">{getLevelLabel(skill.proficiency_level)}</strong>
                    </span>

                    <div className="flex items-center gap-1">
                      {[1, 2, 3, 4, 5].map((lvl) => (
                        <button
                          key={lvl}
                          onClick={() => handleUpdateProficiency(skill.id, lvl)}
                          className={`w-5 h-5 rounded text-[10px] font-bold transition-colors ${
                            skill.proficiency_level === lvl
                              ? 'bg-sky-500 text-slate-950'
                              : 'bg-slate-800 hover:bg-slate-700 text-slate-400'
                          }`}
                        >
                          {lvl}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Manual Skill Addition Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Add Custom / Missing Skill</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Skill Name</label>
              <input
                type="text"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                placeholder="e.g. GraphQL, PyTorch, Kubernetes"
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
              <select
                value={newSkillCategory}
                onChange={(e) => setNewSkillCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-sm"
              >
                <option value="Programming Languages">Programming Languages</option>
                <option value="Web Development">Web Development</option>
                <option value="Database Technologies">Database Technologies</option>
                <option value="AI and Machine Learning">AI and Machine Learning</option>
                <option value="Development Tools & DevOps">Development Tools & DevOps</option>
                <option value="Cloud Platforms">Cloud Platforms</option>
                <option value="Professional & Soft Skills">Professional & Soft Skills</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Self-Reported Proficiency</label>
              <div className="grid grid-cols-5 gap-1">
                {[1, 2, 3, 4, 5].map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setNewSkillLevel(lvl)}
                    className={`py-1.5 rounded text-xs font-bold ${
                      newSkillLevel === lvl ? 'bg-sky-500 text-slate-950' : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    L{lvl}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleAddManualSkill}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-sky-500 hover:bg-sky-400 text-slate-950"
              >
                Add Skill
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
