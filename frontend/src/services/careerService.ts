import { apiClient } from './api';
import { CareerRoleSummary, CareerRoleDetail, CareerMatchResponse, UserCareerGoal } from '../types/career';

export const careerService = {
  async listRoles(): Promise<CareerRoleSummary[]> {
    const res = await apiClient.get<CareerRoleSummary[]>('/careers/roles');
    return res.data;
  },

  async getRole(roleId: string): Promise<CareerRoleDetail> {
    const res = await apiClient.get<CareerRoleDetail>(`/careers/roles/${roleId}`);
    return res.data;
  },

  async matchCareer(roleId: string): Promise<CareerMatchResponse> {
    const res = await apiClient.get<CareerMatchResponse>(`/careers/roles/${roleId}/match`);
    return res.data;
  },

  async setCareerGoal(careerRoleId: string, targetDate?: string): Promise<UserCareerGoal> {
    const res = await apiClient.post<UserCareerGoal>('/careers/goals', {
      career_role_id: careerRoleId,
      target_completion_date: targetDate,
    });
    return res.data;
  },

  async getActiveGoal(): Promise<UserCareerGoal | null> {
    const res = await apiClient.get<UserCareerGoal | null>('/careers/goals/me');
    return res.data;
  },
};
