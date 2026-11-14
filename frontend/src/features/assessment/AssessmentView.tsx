import React, { useState, useEffect } from 'react';
import { assessmentService } from '../../services/assessmentService';
import {
  AssessmentDetailResponse,
  AnswerSubmissionItem,
  AssessmentResultResponse
} from '../../types/assessment';

interface AssessmentViewProps {
  milestoneId: string;
  milestoneTitle?: string;
  onBackToRoadmap: () => void;
}

export const AssessmentView: React.FC<AssessmentViewProps> = ({
  milestoneId,
  milestoneTitle,
  onBackToRoadmap,
}) => {
  const [assessment, setAssessment] = useState<AssessmentDetailResponse | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AssessmentResultResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadQuiz();
  }, [milestoneId]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      setResult(null);
      setSelectedAnswers({});
      const data = await assessmentService.getMilestoneQuiz(milestoneId);
      setAssessment(data);
    } catch (err: any) {
      console.error('Failed to load assessment:', err);
      setErrorMsg('Failed to load assessment quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (questionId: string, optionId: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  };

  const handleSubmit = async () => {
    if (!assessment) return;

    // Check all answered
    const unansweredCount = assessment.questions.filter((q) => !selectedAnswers[q.id]).length;
    if (unansweredCount > 0) {
      setErrorMsg(`Please answer all ${assessment.questions.length} questions before submitting.`);
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      const answerList: AnswerSubmissionItem[] = assessment.questions.map((q) => ({
        question_id: q.id,
        selected_option_id: selectedAnswers[q.id],
      }));

      const res = await assessmentService.submitQuiz(assessment.id, answerList);
      setResult(res);
    } catch (err: any) {
      console.error('Submission failed:', err);
      setErrorMsg('Failed to submit assessment: ' + (err.message || 'Server error'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mr-3"></div>
        Preparing competency assessment questions...
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="max-w-2xl mx-auto p-8 text-center bg-slate-900 border border-slate-800 rounded-2xl my-8">
        <p className="text-slate-400 text-sm">{errorMsg || 'No assessment questions available.'}</p>
        <button
          onClick={onBackToRoadmap}
          className="mt-4 px-4 py-2 bg-slate-800 text-slate-200 rounded-xl text-sm"
        >
          ← Return to Learning Roadmap
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 p-6">
      {/* Quiz Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              Competency Evaluation {milestoneTitle ? `• ${milestoneTitle}` : ''}
            </div>
            <h2 className="text-xl font-bold text-white mt-0.5">{assessment.title}</h2>
            <p className="text-xs text-slate-400 mt-1">
              Passing threshold: <span className="text-emerald-400 font-semibold">{assessment.passing_score}%</span> • Questions: {assessment.questions.length}
            </p>
          </div>

          <button
            onClick={onBackToRoadmap}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
          >
            ← Back
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl border bg-rose-950/40 border-rose-800 text-rose-300 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Result Card when submitted */}
      {result && (
        <div
          className={`p-6 rounded-2xl border ${
            result.passed
              ? 'bg-emerald-950/20 border-emerald-800/60'
              : 'bg-rose-950/20 border-rose-800/60'
          } space-y-4`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold ${
                  result.passed
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                }`}
              >
                {result.passed ? '✓' : '✗'}
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">
                  {result.passed ? 'Assessment Passed!' : 'Remedial Review Required'}
                </h3>
                <p className="text-xs text-slate-400">
                  Score: <span className="text-white font-bold">{result.percentage}%</span> ({result.total_score}/{result.max_score} points)
                </p>
              </div>
            </div>

            <span
              className={`px-3 py-1 rounded-full text-xs font-bold border ${
                result.passed
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                  : 'bg-rose-950 text-rose-300 border-rose-800'
              }`}
            >
              {result.status}
            </span>
          </div>

          {/* AI Evaluator Feedback */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
            <div className="font-semibold text-indigo-400 mb-1 flex items-center gap-1.5">
              <span>✦</span> AI Assessment Evaluator Diagnostic
            </div>
            {result.ai_evaluator_feedback}
          </div>

          {result.adaptive_action && (
            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-center gap-2">
              <span className="text-indigo-400 font-bold">⚡ Adaptive System:</span> {result.adaptive_action}
            </div>
          )}

          <div className="pt-2 flex items-center gap-3">
            <button
              onClick={onBackToRoadmap}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all"
            >
              Return to Learning Roadmap →
            </button>
            {!result.passed && (
              <button
                onClick={loadQuiz}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium border border-slate-700 transition-colors"
              >
                Retake Assessment ↺
              </button>
            )}
          </div>
        </div>
      )}

      {/* Question Form */}
      {!result && (
        <div className="space-y-6">
          {assessment.questions.map((q, idx) => (
            <div key={q.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-lg bg-indigo-950 border border-indigo-800/50 flex items-center justify-center text-xs font-bold text-indigo-400 shrink-0">
                  {idx + 1}
                </span>
                <div className="text-sm font-medium text-slate-100 leading-relaxed">{q.question_text}</div>
              </div>

              {/* Options */}
              <div className="space-y-2.5 pt-2 pl-9">
                {q.options.map((opt) => {
                  const isSelected = selectedAnswers[q.id] === opt.id;
                  return (
                    <label
                      key={opt.id}
                      onClick={() => handleSelectOption(q.id, opt.id)}
                      className={`flex items-center gap-3 p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-indigo-600/15 border-indigo-500 text-white'
                          : 'bg-slate-950/40 border-slate-800/80 text-slate-300 hover:border-slate-700 hover:bg-slate-950/70'
                      }`}
                    >
                      <input
                        type="radio"
                        name={q.id}
                        checked={isSelected}
                        onChange={() => handleSelectOption(q.id, opt.id)}
                        className="text-indigo-600 focus:ring-indigo-500 h-4 w-4 bg-slate-900 border-slate-700"
                      />
                      <span>{opt.option_text}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Submit Action */}
          <div className="pt-2 flex justify-end">
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/20 transition-all flex items-center gap-2"
            >
              {submitting ? 'Scoring Assessment...' : 'Submit Answers & Receive AI Feedback →'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
