import React, { useState } from 'react';
import { authService } from '../../services/authService';
import { UserRole } from '../../types/auth';

interface RegisterPageProps {
  onSuccess: () => void;
  onNavigateToLogin: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onSuccess, onNavigateToLogin }) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<UserRole>('STUDENT');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);

    try {
      await authService.register({
        full_name: fullName,
        email,
        password,
        confirm_password: confirmPassword,
        role,
      });
      setSuccessMsg(true);
      setTimeout(() => {
        onSuccess();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please check inputs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl">
      <div className="mb-6 text-center">
        <div className="inline-flex w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 items-center justify-center font-bold text-lg mb-3">
          🎓
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Create Account</h2>
        <p className="text-sm text-slate-400 mt-1">
          Join the AI-powered adaptive learning journey
        </p>
      </div>

      {error && (
        <div className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="mb-5 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
          <span>✅</span>
          <span>Registration successful! Redirecting to sign in...</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
            Full Name
          </label>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Alex Mercer"
            className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500 transition-colors text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
            Email Address
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="alex@domain.com"
            className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500 transition-colors text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
            Platform Role
          </label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500 transition-colors text-sm"
          >
            <option value="STUDENT">Student / Learner</option>
            <option value="MENTOR">Industry Mentor</option>
            <option value="ORG_ADMIN">Organization Administrator</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500 transition-colors text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Confirm
            </label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500 transition-colors text-sm"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || successMsg}
          className="w-full mt-2 py-2.5 px-4 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              <span>Registering...</span>
            </>
          ) : (
            <span>Create Account</span>
          )}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-slate-800/80 text-center">
        <p className="text-xs text-slate-400">
          Already have an account?{' '}
          <button
            onClick={onNavigateToLogin}
            className="text-sky-400 hover:text-sky-300 font-medium underline underline-offset-4 transition-colors"
          >
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
};
