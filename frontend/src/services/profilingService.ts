import { apiClient } from './api';
import {
  DocumentUploadResponse,
  ProfilePreviewResponse,
  ExtractedSkillItem,
  ProfilingStatusResponse,
  ProfileConfirmResponse
} from '../types/profiling';

export const profilingService = {
  async uploadResume(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<DocumentUploadResponse>('/profiling/resume/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async extractSkills(rawText?: string, useCachedResume: boolean = true): Promise<ProfilePreviewResponse> {
    const response = await apiClient.post<ProfilePreviewResponse>('/profiling/extract', {
      raw_text: rawText,
      use_cached_resume: useCachedResume,
    });
    return response.data;
  },

  async getPreview(): Promise<ProfilePreviewResponse> {
    const response = await apiClient.get<ProfilePreviewResponse>('/profiling/preview');
    return response.data;
  },

  async updateSkill(
    skillId: string,
    data: {
      proficiency_level?: number;
      is_confirmed?: boolean;
      is_rejected?: boolean;
      user_notes?: string;
    }
  ): Promise<ExtractedSkillItem> {
    const response = await apiClient.patch<ExtractedSkillItem>(`/profiling/skills/${skillId}`, data);
    return response.data;
  },

  async confirmProfile(confirmedSkillIds?: string[]): Promise<ProfileConfirmResponse> {
    const response = await apiClient.post<ProfileConfirmResponse>('/profiling/confirm', {
      confirmed_skill_ids: confirmedSkillIds,
    });
    return response.data;
  },

  async getStatus(): Promise<ProfilingStatusResponse> {
    const response = await apiClient.get<ProfilingStatusResponse>('/profiling/status');
    return response.data;
  },
};
