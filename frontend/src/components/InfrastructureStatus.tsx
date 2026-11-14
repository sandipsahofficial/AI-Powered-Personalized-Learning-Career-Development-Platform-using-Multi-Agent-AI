import React, { useState, useEffect, useCallback } from 'react';
import { 
  Server, 
  Database, 
  Cpu, 
  Layers, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Activity,
  Terminal,
  ShieldCheck,
  Clock
} from 'lucide-react';
import { healthService } from '../services/healthService';
import {
  OverallHealthResponse,
  DatabaseHealthResponse,
  RedisHealthResponse,
  LLMHealthResponse,
  SystemInfoResponse
} from '../types/infrastructure';

export const InfrastructureStatus: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  // Real Service Health States
  const [overallHealth, setOverallHealth] = useState<OverallHealthResponse | null>(null);
  const [dbHealth, setDbHealth] = useState<DatabaseHealthResponse | null>(null);
  const [redisHealth, setRedisHealth] = useState<RedisHealthResponse | null>(null);
  const [llmHealth, setLlmHealth] = useState<LLMHealthResponse | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfoResponse | null>(null);
  
  // Individual errors
  const [backendError, setBackendError] = useState<string | null>(null);
  const [dbError, setDbError] = useState<string | null>(null);
  const [redisError, setRedisError] = useState<string | null>(null);
  const [llmError, setLlmError] = useState<string | null>(null);

  const fetchInfrastructureStatus = useCallback(async () => {
    setLoading(true);
    setBackendError(null);
    setDbError(null);
    setRedisError(null);
    setLlmError(null);

    // 1. Overall Backend Check
    try {
      const overall = await healthService.getOverallHealth();
      setOverallHealth(overall);
    } catch (err: any) {
      setBackendError(err.message || 'Cannot reach FastAPI backend server');
      setOverallHealth(null);
    }

    // 2. Database Check
    try {
      const db = await healthService.getDatabaseHealth();
      setDbHealth(db);
    } catch (err: any) {
      setDbError(err.message || (err.data?.error ? err.data.error : 'Database check failed'));
      setDbHealth(null);
    }

    // 3. Redis Check
    try {
      const redis = await healthService.getRedisHealth();
      setRedisHealth(redis);
    } catch (err: any) {
      setRedisError(err.message || (err.data?.error ? err.data.error : 'Redis check failed'));
      setRedisHealth(null);
    }

    // 4. Ollama LLM Check
    try {
      const llm = await healthService.getLLMHealth();
      setLlmHealth(llm);
    } catch (err: any) {
      setLlmError(err.message || (err.data?.error ? err.data.error : 'Ollama LLM unreachable'));
      setLlmHealth(null);
    }

    // 5. System Info
    try {
      const sys = await healthService.getSystemInfo();
      setSystemInfo(sys);
    } catch {
      setSystemInfo(null);
    }

    setLastUpdated(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchInfrastructureStatus();
  }, [fetchInfrastructureStatus]);

  const renderBadge = (status: 'healthy' | 'degraded' | 'unhealthy' | 'unreachable' | 'unknown') => {
    switch (status) {
      case 'healthy':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5" /> Operational
          </span>
        );
      case 'degraded':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800">
            <AlertTriangle className="w-3.5 h-3.5" /> Degraded
          </span>
        );
      case 'unreachable':
      case 'unhealthy':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
            <XCircle className="w-3.5 h-3.5" /> Offline
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <Activity className="w-3.5 h-3.5 animate-pulse" /> Checking...
          </span>
        );
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950 text-sky-400 border border-sky-800 text-xs font-mono uppercase tracking-wider mb-2">
            Phase 2: Core Infrastructure
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Environment & Infrastructure Status
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time live telemetry inspecting Docker services, API Gateway, PostgreSQL + pgvector, Redis, and Ollama.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastUpdated && (
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {lastUpdated.toLocaleTimeString()}
            </div>
          )}
          <button
            onClick={fetchInfrastructureStatus}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-medium text-sm transition-colors shadow-lg shadow-sky-900/20"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Probing...' : 'Re-verify All'}
          </button>
        </div>
      </div>

      {/* Grid of Core Infrastructure Components */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Frontend */}
        <div className="p-5 rounded-xl bg-slate-800/60 border border-slate-700/80 shadow-sm flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="p-2.5 rounded-lg bg-sky-950/70 text-sky-400 border border-sky-800/50">
                <Layers className="w-5 h-5" />
              </span>
              {renderBadge('healthy')}
            </div>
            <div>
              <h3 className="font-semibold text-white">Frontend Client</h3>
              <p className="text-xs text-slate-400 mt-0.5">React 18 + Vite + TS</p>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700/50 text-xs font-mono text-slate-300">
            <div>Port: 5173</div>
            <div className="text-emerald-400 mt-0.5">DOM Mounted & Active</div>
          </div>
        </div>

        {/* 2. Backend FastAPI */}
        <div className="p-5 rounded-xl bg-slate-800/60 border border-slate-700/80 shadow-sm flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="p-2.5 rounded-lg bg-indigo-950/70 text-indigo-400 border border-indigo-800/50">
                <Server className="w-5 h-5" />
              </span>
              {renderBadge(overallHealth ? 'healthy' : 'unreachable')}
            </div>
            <div>
              <h3 className="font-semibold text-white">FastAPI Backend</h3>
              <p className="text-xs text-slate-400 mt-0.5">Python 3.11+ / Uvicorn</p>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700/50 text-xs font-mono text-slate-300">
            {overallHealth ? (
              <>
                <div>Env: {overallHealth.environment}</div>
                <div>Version: {overallHealth.version}</div>
              </>
            ) : (
              <div className="text-rose-400 truncate">{backendError || 'Offline'}</div>
            )}
          </div>
        </div>

        {/* 3. PostgreSQL + pgvector */}
        <div className="p-5 rounded-xl bg-slate-800/60 border border-slate-700/80 shadow-sm flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="p-2.5 rounded-lg bg-blue-950/70 text-blue-400 border border-blue-800/50">
                <Database className="w-5 h-5" />
              </span>
              {renderBadge(dbHealth?.status === 'healthy' ? 'healthy' : 'unreachable')}
            </div>
            <div>
              <h3 className="font-semibold text-white">PostgreSQL + pgvector</h3>
              <p className="text-xs text-slate-400 mt-0.5">Relational & Vector Store</p>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700/50 text-xs font-mono text-slate-300">
            {dbHealth?.status === 'healthy' ? (
              <>
                <div className="text-emerald-400">pgvector: {dbHealth.pgvector_version}</div>
                <div>Pool: {dbHealth.pool_size} connections</div>
              </>
            ) : (
              <div className="text-rose-400 truncate">{dbError || 'Connection Refused'}</div>
            )}
          </div>
        </div>

        {/* 4. Redis */}
        <div className="p-5 rounded-xl bg-slate-800/60 border border-slate-700/80 shadow-sm flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="p-2.5 rounded-lg bg-red-950/70 text-red-400 border border-red-800/50">
                <Activity className="w-5 h-5" />
              </span>
              {renderBadge(redisHealth?.status === 'healthy' ? 'healthy' : 'unreachable')}
            </div>
            <div>
              <h3 className="font-semibold text-white">Redis 7 In-Memory</h3>
              <p className="text-xs text-slate-400 mt-0.5">Cache & Session Denylist</p>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700/50 text-xs font-mono text-slate-300">
            {redisHealth?.status === 'healthy' ? (
              <>
                <div>Latency: {redisHealth.latency_ms} ms</div>
                <div className="text-emerald-400">R/W: Verified</div>
              </>
            ) : (
              <div className="text-rose-400 truncate">{redisError || 'Connection Refused'}</div>
            )}
          </div>
        </div>
      </div>

      {/* Ollama Local LLM Deep Telemetry */}
      <div className="p-6 rounded-xl bg-slate-800/40 border border-slate-700/70 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-lg bg-purple-950/70 text-purple-400 border border-purple-800/50">
              <Cpu className="w-6 h-6" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-white">Ollama Local LLM Connectivity</h2>
              <p className="text-xs text-slate-400">Endpoint: {llmHealth?.ollama_base_url || 'http://localhost:11434'}</p>
            </div>
          </div>
          {renderBadge(
            llmHealth?.status === 'healthy' 
              ? 'healthy' 
              : llmHealth?.status === 'unreachable' 
                ? 'unreachable' 
                : 'degraded'
          )}
        </div>

        {llmHealth?.status === 'healthy' ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-mono">
              <span className="text-slate-400 block mb-1">Inference Latency:</span>
              <span className="text-emerald-400 font-semibold">{llmHealth.latency_ms} ms</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-mono">
              <span className="text-slate-400 block mb-1">Installed Models ({llmHealth.total_models}):</span>
              <span className="text-sky-300 font-semibold truncate block">
                {llmHealth.installed_models?.join(', ') || 'None found'}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-mono">
              <span className="text-slate-400 block mb-1">Configured Target Models:</span>
              <span className="text-slate-200">
                Instruction: {llmHealth.configured_models?.instruction}<br />
                Reasoning: {llmHealth.configured_models?.reasoning}
              </span>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-lg bg-amber-950/40 border border-amber-800/60 text-xs text-amber-200 space-y-1 font-mono">
            <div className="font-semibold flex items-center gap-2 text-amber-300">
              <AlertTriangle className="w-4 h-4" /> Ollama Service Status: {llmHealth?.status || 'Unreachable'}
            </div>
            <p className="text-slate-300">{llmError || 'Host Ollama daemon is currently inactive or running on alternative port.'}</p>
            <p className="text-slate-400 text-[11px] pt-1">
              Hint: Start Ollama on the host via <code className="text-amber-300">ollama serve</code> or start the container via <code className="text-amber-300">docker-compose up -d ollama</code>.
            </p>
          </div>
        )}
      </div>

      {/* System Telemetry & Sanitized Runtime Info */}
      {systemInfo && (
        <div className="p-6 rounded-xl bg-slate-800/30 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
            <Terminal className="w-4 h-4 text-sky-400" /> Sanitized Runtime Telemetry
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono text-slate-400 pt-1">
            <div>
              <span className="text-slate-500 block">Host OS:</span>
              <span className="text-slate-200">{systemInfo.platform.os} ({systemInfo.platform.architecture})</span>
            </div>
            <div>
              <span className="text-slate-500 block">Python Runtime:</span>
              <span className="text-slate-200">{systemInfo.runtime.python_version}</span>
            </div>
            <div>
              <span className="text-slate-500 block">CPU Cores:</span>
              <span className="text-slate-200">{systemInfo.platform.cpu_count} Threads</span>
            </div>
            <div>
              <span className="text-slate-500 block">Security Baseline:</span>
              <span className="text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> No Secrets Exposed
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
