import React, { useState, useEffect } from 'react';
import { InfrastructureStatus } from './components/InfrastructureStatus';
import { LoginPage } from './features/auth/LoginPage';
import { RegisterPage } from './features/auth/RegisterPage';
import { LearnerDashboardView } from './features/dashboard/LearnerDashboardView';
import { LearnerProfilingView } from './features/profiling/LearnerProfilingView';
import { CareerPathView } from './features/career/CareerPathView';
import { RoadmapView } from './features/roadmap/RoadmapView';
import { AssessmentView } from './features/assessment/AssessmentView';
import { AIMentorView } from './features/mentor/AIMentorView';
import { authService } from './services/authService';
import { User } from './types/auth';

type ViewMode =
  | 'login'
  | 'register'
  | 'portal'
  | 'profiling'
  | 'career'
  | 'roadmap'
  | 'assessment'
  | 'mentor'
  | 'infrastructure';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<ViewMode>('login');
  const [activeAssessment, setActiveAssessment] = useState<{ id: string; title: string } | null>(null);

  useEffect(() => {
    const savedUser = authService.getCurrentUser();
    if (savedUser && authService.isAuthenticated()) {
      setUser(savedUser);
      setView('portal');
    }
  }, []);

  const handleLoginSuccess = (authenticatedUser: User) => {
    setUser(authenticatedUser);
    setView('portal');
  };

  const handleLogout = async () => {
    await authService.logout();
    setUser(null);
    setView('login');
  };

  const handleStartAssessment = (milestoneId: string, milestoneTitle: string) => {
    setActiveAssessment({ id: milestoneId, title: milestoneTitle });
    setView('assessment');
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => setView(user ? 'portal' : 'login')}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-sky-400 flex items-center justify-center font-bold text-slate-950 text-sm shadow-md shadow-indigo-500/20">
              ✦
            </div>
            <span className="font-semibold text-white tracking-tight text-sm hidden sm:inline">
              AI Personalized Learning & Career Platform
            </span>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto py-1">
            {!user ? (
              <button
                onClick={() => setView('login')}
                className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  view === 'login' || view === 'register'
                    ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Sign In
              </button>
            ) : (
              <>
                <button
                  onClick={() => setView('portal')}
                  className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                    view === 'portal'
                      ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  My Portal
                </button>

                <button
                  onClick={() => setView('profiling')}
                  className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                    view === 'profiling'
                      ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Skill Profiler
                </button>

                <button
                  onClick={() => setView('career')}
                  className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                    view === 'career'
                      ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Career Match
                </button>

                <button
                  onClick={() => setView('roadmap')}
                  className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                    view === 'roadmap'
                      ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Roadmap
                </button>

                <button
                  onClick={() => setView('mentor')}
                  className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                    view === 'mentor'
                      ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  AI Mentor ✦
                </button>
              </>
            )}

            <button
              onClick={() => setView('infrastructure')}
              className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                view === 'infrastructure'
                  ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Infrastructure
            </button>

            {user && (
              <button
                onClick={handleLogout}
                className="ml-2 text-xs px-2.5 py-1.5 rounded-lg text-rose-400 hover:bg-rose-500/10 border border-rose-500/20 transition-colors"
              >
                Sign Out
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full py-6">
        {view === 'login' && (
          <div className="flex items-center justify-center min-h-[70vh]">
            <LoginPage
              onSuccess={handleLoginSuccess}
              onNavigateToRegister={() => setView('register')}
            />
          </div>
        )}

        {view === 'register' && (
          <div className="flex items-center justify-center min-h-[70vh]">
            <RegisterPage
              onSuccess={() => setView('login')}
              onNavigateToLogin={() => setView('login')}
            />
          </div>
        )}

        {view === 'portal' && user && (
          <LearnerDashboardView
            onNavigateTab={(tab) => {
              if (tab === 'profiling') setView('profiling');
              else if (tab === 'careers') setView('career');
              else if (tab === 'roadmap') setView('roadmap');
              else if (tab === 'mentor') setView('mentor');
            }}
          />
        )}

        {view === 'profiling' && user && <LearnerProfilingView />}

        {view === 'career' && user && (
          <CareerPathView onNavigateToRoadmap={() => setView('roadmap')} />
        )}

        {view === 'roadmap' && user && (
          <RoadmapView
            onStartAssessment={handleStartAssessment}
            onNavigateToCareers={() => setView('career')}
          />
        )}

        {view === 'assessment' && user && activeAssessment && (
          <AssessmentView
            milestoneId={activeAssessment.id}
            milestoneTitle={activeAssessment.title}
            onBackToRoadmap={() => setView('roadmap')}
          />
        )}

        {view === 'mentor' && user && <AIMentorView />}

        {view === 'infrastructure' && (
          <div className="flex items-center justify-center min-h-[60vh]">
            <InfrastructureStatus />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-4 text-center text-xs text-slate-500">
        AI-Powered Personalized Learning & Career Development Platform &bull; Multi-Agent AI System &bull; Production Ready
      </footer>
    </div>
  );
};

export default App;
