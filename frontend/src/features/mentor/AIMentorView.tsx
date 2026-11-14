import React, { useState, useEffect, useRef } from 'react';
import { mentorService } from '../../services/mentorService';
import { careerService } from '../../services/careerService';
import { roadmapService } from '../../services/roadmapService';
import { ChatMessage } from '../../types/mentor';

export const AIMentorView: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [sending, setSending] = useState<boolean>(false);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [activeRole, setActiveRole] = useState<string>('Target Career');
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [currentMilestone, setCurrentMilestone] = useState<string>('Phase 1: Core Web Foundations');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedPrompts = [
    'What should I focus on next for my career goal?',
    'How do I prepare for technical interviews for this role?',
    'Explain why my missing skills are critical in production.',
    'What real-world project deliverable should I build next?',
  ];

  useEffect(() => {
    loadContextAndHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const loadContextAndHistory = async () => {
    try {
      setLoadingHistory(true);

      // Load Goal & Match
      const goal = await careerService.getActiveGoal();
      if (goal) {
        setActiveRole(goal.career_role_title);
        setReadinessScore(goal.match_percentage || null);
      }

      // Load Active Roadmap
      const roadmap = await roadmapService.getActiveRoadmap();
      if (roadmap && roadmap.milestones.length > 0) {
        const active = roadmap.milestones.find((m) => m.status === 'IN_PROGRESS' || m.status === 'REMEDIAL');
        if (active) {
          setCurrentMilestone(`${active.title} (${active.status})`);
        }
      }

      // Load Chat History
      const hist = await mentorService.getHistory();
      if (hist && hist.messages && hist.messages.length > 0) {
        setMessages(hist.messages as ChatMessage[]);
      } else {
        // Default warm welcome
        setMessages([
          {
            role: 'assistant',
            content: `Hello! I am your AI Career Mentor. I have reviewed your confirmed skills, your target role of **${goal?.career_role_title || 'Software Engineering'}**, and your current learning roadmap.\n\nAsk me anything about mastering challenging technical concepts, structuring portfolio projects, or preparing for interviews!`,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (err: any) {
      console.error('Failed to load mentorship context:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || sending) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setSending(true);

    try {
      const res = await mentorService.chatWithMentor(text);
      const mentorMsg: ChatMessage = {
        role: 'assistant',
        content: res.reply,
        timestamp: res.timestamp,
      };
      setMessages((prev) => [...prev, mentorMsg]);
      if (res.active_role) setActiveRole(res.active_role);
      if (res.readiness_percentage !== undefined && res.readiness_percentage !== null) {
        setReadinessScore(res.readiness_percentage);
      }
      if (res.current_milestone) setCurrentMilestone(res.current_milestone);
    } catch (err: any) {
      console.error('Chat failed:', err);
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: 'I encountered an issue connecting to the AI inference service. Please verify local Ollama connectivity.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 p-6">
      {/* Mentor Header & Live Learner Context Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white text-lg font-bold shadow-lg shadow-indigo-600/20">
              ✦
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">AI Career Mentor & Technical Coach</h2>
              <p className="text-xs text-slate-400">Context-aware multi-agent guidance tailored to your learning data</p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-indigo-300 font-medium">
              Goal: {activeRole}
            </span>
            {readinessScore !== null && (
              <span className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-emerald-400 font-medium">
                {readinessScore}% Match
              </span>
            )}
          </div>
        </div>

        {/* Current Active Milestone Telemetry */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center gap-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Active Learning Focus:</span>
          <span className="text-slate-200 font-medium">{currentMilestone}</span>
        </div>
      </div>

      {/* Suggested Prompt Pills */}
      <div className="flex flex-wrap gap-2">
        {suggestedPrompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSendMessage(prompt)}
            disabled={sending}
            className="px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs transition-colors text-left"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Chat Messages Container */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 min-h-[420px] max-h-[560px] overflow-y-auto space-y-4">
        {loadingHistory ? (
          <div className="flex justify-center items-center py-20 text-slate-400 text-xs">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-500 mr-2"></div>
            Restoring mentorship conversation context...
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={idx}
                className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-xs text-indigo-300 shrink-0 font-bold">
                    ✦
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? 'bg-indigo-600 text-white rounded-tr-none'
                      : 'bg-slate-950/70 text-slate-200 border border-slate-800 rounded-tl-none'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            );
          })
        )}

        {sending && (
          <div className="flex gap-3 justify-start items-center">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-xs text-indigo-300 shrink-0 font-bold">
              ✦
            </div>
            <div className="bg-slate-950/70 border border-slate-800 rounded-2xl p-3 text-xs text-slate-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></div>
              Synthesizing personalized mentorship advice...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-2.5 flex items-center gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask your AI Mentor about roadmap milestones, technologies, or interview readiness..."
          disabled={sending}
          className="flex-1 bg-transparent border-0 px-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-0"
        />
        <button
          onClick={() => handleSendMessage()}
          disabled={sending || !inputText.trim()}
          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold rounded-xl transition-all shadow-md shadow-indigo-600/20"
        >
          Send →
        </button>
      </div>
    </div>
  );
};
