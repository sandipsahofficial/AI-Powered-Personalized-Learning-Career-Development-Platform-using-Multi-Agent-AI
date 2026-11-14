export interface SkillEvidence {
  evidence_type: 'PROJECT_DEMONSTRATED' | 'CERTIFICATION_SUPPORTED' | 'EXPERIENCE_INFERRED' | 'EXPLICITLY_DECLARED' | 'INSUFFICIENT_EVIDENCE';
  source_section: string;
  original_phrase: string;
  description: string;
  confidence_score: number;
}

export interface ExtractedSkillItem {
  id: string;
  canonical_name: string;
  category: string;
  original_phrase: string;
  proficiency_level: number | null; // 1 to 5
  proficiency_status: 'ESTIMATED' | 'INSUFFICIENT_EVIDENCE' | 'USER_CONFIRMED' | 'USER_OVERRIDDEN';
  confidence_score: number;
  evidence: SkillEvidence[];
  normalization_method: string;
  is_confirmed: boolean;
  is_rejected: boolean;
  user_notes?: string | null;
}

export interface DocumentSection {
  title: string;
  content: string;
  char_count: number;
}

export interface DocumentUploadResponse {
  filename: string;
  file_type: string;
  size_bytes: number;
  char_count: number;
  sections_detected: string[];
  sections: DocumentSection[];
  extracted_text_preview: string;
  upload_timestamp: string;
}

export interface ProfilePreviewResponse {
  user_id: string;
  extracted_skills: ExtractedSkillItem[];
  total_skills_count: number;
  categories_breakdown: Record<string, number>;
  ai_model_used: string;
  is_fallback: boolean;
  extraction_timestamp: string;
  document_summary?: {
    headline?: string;
    summary?: string;
  } | null;
}

export interface ProfilingStatusResponse {
  has_uploaded_resume: boolean;
  last_uploaded_filename?: string | null;
  last_extracted_at?: string | null;
  total_skills_in_preview: number;
  confirmed_skills_count: number;
  pending_review_count: number;
  total_persisted_skills: number;
}

export interface ProfileConfirmResponse {
  user_id: string;
  persisted_count: number;
  updated_count: number;
  total_skills_in_profile: number;
  status: string;
  message: string;
}
