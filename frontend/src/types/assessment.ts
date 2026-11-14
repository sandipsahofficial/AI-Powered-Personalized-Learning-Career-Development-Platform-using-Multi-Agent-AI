export interface AssessmentOptionItem {
  id: string;
  option_text: string;
}

export interface AssessmentQuestionItem {
  id: string;
  question_text: string;
  points: number;
  order_index: number;
  options: AssessmentOptionItem[];
}

export interface AssessmentDetailResponse {
  id: string;
  milestone_id: string;
  milestone_title: string;
  title: string;
  passing_score: number;
  time_limit_minutes?: number;
  questions: AssessmentQuestionItem[];
}

export interface AnswerSubmissionItem {
  question_id: string;
  selected_option_id: string;
}

export interface AssessmentResultResponse {
  attempt_id: string;
  assessment_id: string;
  milestone_id: string;
  total_score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  status: 'PASSED' | 'REMEDIAL_REQUIRED';
  ai_evaluator_feedback: string;
  adaptive_action?: string;
  evaluated_at: string;
}

export interface ProgressSummaryResponse {
  user_id: string;
  target_career_title?: string;
  readiness_percentage: number;
  confirmed_skills_count: number;
  active_roadmap_title?: string;
  roadmap_progress_percentage: number;
  completed_milestones_count: number;
  total_milestones_count: number;
  assessments_taken_count: number;
  assessments_passed_count: number;
  recent_assessment?: AssessmentResultResponse;
}
