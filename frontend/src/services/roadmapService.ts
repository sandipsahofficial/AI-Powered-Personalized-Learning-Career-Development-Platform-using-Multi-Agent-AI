import { apiClient } from './api';
import { LearningRoadmapResponse, CuratedResourceItem } from '../types/roadmap';

export const roadmapService = {
  async generateRoadmap(careerRoleId: string, forceRecreate = false): Promise<LearningRoadmapResponse> {
    const res = await apiClient.post<LearningRoadmapResponse>(
      `/roadmaps/generate?force_recreate=${forceRecreate}`,
      { career_role_id: careerRoleId }
    );
    return res.data;
  },

  async getActiveRoadmap(): Promise<LearningRoadmapResponse | null> {
    const res = await apiClient.get<LearningRoadmapResponse | null>('/roadmaps/active');
    return res.data;
  },

  async updateMilestoneStatus(
    milestoneId: string,
    status: 'LOCKED' | 'IN_PROGRESS' | 'REVIEW_PENDING' | 'COMPLETED' | 'REMEDIAL'
  ): Promise<LearningRoadmapResponse> {
    const res = await apiClient.patch<LearningRoadmapResponse>(
      `/roadmaps/milestones/${milestoneId}/status`,
      { status }
    );
    return res.data;
  },

  async getRecommendedResources(): Promise<CuratedResourceItem[]> {
    const res = await apiClient.get<CuratedResourceItem[]>('/roadmaps/resources/recommended');
    return res.data;
  },
};
