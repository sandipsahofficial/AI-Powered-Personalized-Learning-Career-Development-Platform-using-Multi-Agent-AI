import { apiClient } from './api';
import {
  AssessmentDetailResponse,
  AnswerSubmissionItem,
  AssessmentResultResponse,
  ProgressSummaryResponse
} from '../types/assessment';

export const assessmentService = {
  async getMilestoneQuiz(milestoneId: string): Promise<AssessmentDetailResponse> {
    const res = await apiClient.get<AssessmentDetailResponse>(`/assessments/milestones/${milestoneId}`);
    return res.data;
  },

  async submitQuiz(assessmentId: string, answers: AnswerSubmissionItem[]): Promise<AssessmentResultResponse> {
    const res = await apiClient.post<AssessmentResultResponse>('/assessments/submit', {
      assessment_id: assessmentId,
      answers,
    });
    return res.data;
  },

  async getProgressSummary(): Promise<ProgressSummaryResponse> {
    const res = await apiClient.get<ProgressSummaryResponse>('/assessments/progress/summary');
    return res.data;
  },
};
