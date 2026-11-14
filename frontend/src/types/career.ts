export interface CareerRoleSummary {
  id: string;
  title: string;
  slug: string;
  category_name?: string;
  industry_demand_level: string;
  average_salary_range?: string;
  description?: string;
}

export interface SkillRequirementItem {
  skill_id: string;
  skill_name: string;
  required_proficiency: number;
  importance_weight: number;
  is_mandatory: boolean;
}

export interface CareerRoleDetail extends CareerRoleSummary {
  skill_requirements: SkillRequirementItem[];
}

export interface SkillGapItem {
  skill_id?: string;
  skill_name: string;
  user_proficiency: number;
  required_proficiency: number;
  importance_weight: number;
  is_mandatory: boolean;
  status: 'MATCHED' | 'WEAK' | 'MISSING';
  gap_level: number;
}

export interface CareerMatchResponse {
  career_role_id: string;
  career_role_title: string;
  category_name?: string;
  match_percentage: number;
  matched_skills_count: number;
  weak_skills_count: number;
  missing_skills_count: number;
  total_required_skills: number;
  matching_skills: SkillGapItem[];
  weak_skills: SkillGapItem[];
  missing_skills: SkillGapItem[];
  gap_summary: {
    role_title: string;
    readiness_verdict: string;
    match_percentage: number;
    matched_count: number;
    weak_count: number;
    missing_count: number;
    mandatory_missing: string[];
    key_recommendation: string;
  };
  computed_at: string;
}

export interface UserCareerGoal {
  id: string;
  user_id: string;
  career_role_id: string;
  career_role_title: string;
  status: string;
  target_completion_date?: string;
  match_percentage?: number;
  created_at: string;
}
