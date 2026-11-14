export interface CuratedResourceItem {
  id: string;
  title: string;
  url: string;
  resource_type: string;
  provider_name?: string;
  rating: number;
  estimated_minutes: number;
  is_free: boolean;
  content_summary?: string;
}

export interface MilestoneResponse {
  id: string;
  phase_number: number;
  order_index: number;
  title: string;
  description?: string;
  deliverable_title?: string;
  deliverable_criteria?: string;
  estimated_hours: number;
  status: 'LOCKED' | 'IN_PROGRESS' | 'REVIEW_PENDING' | 'COMPLETED' | 'REMEDIAL';
  is_remedial: boolean;
  resources: CuratedResourceItem[];
  created_at: string;
}

export interface LearningRoadmapResponse {
  id: string;
  user_id: string;
  career_role_id: string;
  career_role_title: string;
  title: string;
  status: string;
  version: number;
  total_estimated_hours: number;
  progress_percentage: number;
  milestones: MilestoneResponse[];
  created_at: string;
  updated_at?: string;
}
