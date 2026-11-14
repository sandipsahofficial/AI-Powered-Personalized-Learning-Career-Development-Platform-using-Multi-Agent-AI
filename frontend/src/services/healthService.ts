import { apiClient } from './api';
import {
  OverallHealthResponse,
  DatabaseHealthResponse,
  RedisHealthResponse,
  LLMHealthResponse,
  SystemInfoResponse,
} from '../types/infrastructure';

export const healthService = {
  async getOverallHealth(): Promise<OverallHealthResponse> {
    const { data } = await apiClient.get<OverallHealthResponse>('/health');
    return data;
  },

  async getDatabaseHealth(): Promise<DatabaseHealthResponse> {
    const { data } = await apiClient.get<DatabaseHealthResponse>('/health/database');
    return data;
  },

  async getRedisHealth(): Promise<RedisHealthResponse> {
    const { data } = await apiClient.get<RedisHealthResponse>('/health/redis');
    return data;
  },

  async getLLMHealth(): Promise<LLMHealthResponse> {
    const { data } = await apiClient.get<LLMHealthResponse>('/health/llm');
    return data;
  },

  async getSystemInfo(): Promise<SystemInfoResponse> {
    const { data } = await apiClient.get<SystemInfoResponse>('/system/info');
    return data;
  },
};
