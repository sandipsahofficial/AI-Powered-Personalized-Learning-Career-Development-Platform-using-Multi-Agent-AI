export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface MentorChatResponse {
  reply: string;
  timestamp: string;
  active_role?: string;
  readiness_percentage?: number;
  current_milestone?: string;
}

export interface MentorConversationHistoryResponse {
  id: string;
  session_title: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
  }>;
  last_interaction_at: string;
}
