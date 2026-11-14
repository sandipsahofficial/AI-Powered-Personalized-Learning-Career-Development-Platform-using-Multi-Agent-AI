import { apiClient } from './api';
import { MentorChatResponse, MentorConversationHistoryResponse } from '../types/mentor';

export const mentorService = {
  async chatWithMentor(message: string): Promise<MentorChatResponse> {
    const res = await apiClient.post<MentorChatResponse>('/mentor/chat', { message });
    return res.data;
  },

  async getHistory(): Promise<MentorConversationHistoryResponse | null> {
    const res = await apiClient.get<MentorConversationHistoryResponse | null>('/mentor/history');
    return res.data;
  },
};
