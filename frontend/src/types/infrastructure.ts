export interface OverallHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  app_name: string;
  environment: string;
  version: string;
  timestamp: number;
  services: {
    database: string;
    redis: string;
    llm: string;
  };
}

export interface DatabaseHealthResponse {
  status: 'healthy' | 'unhealthy';
  database: string;
  pgvector_installed: boolean;
  pgvector_version?: string;
  pool_size?: number;
  error?: string;
}

export interface RedisHealthResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  ping?: boolean;
  latency_ms?: number;
  read_write_verified?: boolean;
  redis_version?: string;
  connected_clients?: number;
  error?: string;
}

export interface LLMHealthResponse {
  status: 'healthy' | 'unhealthy' | 'unreachable' | 'error';
  ollama_base_url: string;
  latency_ms?: number;
  total_models?: number;
  installed_models?: string[];
  configured_models?: {
    instruction: string;
    reasoning: string;
    embedding: string;
  };
  configured_models_available?: {
    instruction_model: boolean;
    reasoning_model: boolean;
  };
  error?: string;
  hint?: string;
}

export interface SystemInfoResponse {
  platform: {
    os: string;
    os_release: string;
    os_version: string;
    architecture: string;
    cpu_count: number;
  };
  runtime: {
    python_version: string;
    python_compiler: string;
    app_version: string;
    environment: string;
    debug_mode: boolean;
    api_prefix: string;
  };
  network: {
    backend_port: number;
    cors_origins_count: number;
  };
  server_time_utc: string;
}
