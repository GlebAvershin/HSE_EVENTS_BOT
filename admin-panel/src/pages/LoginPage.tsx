import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useAuthStore } from '../stores/authStore';
import type { LoginResponse } from '../types/api';
import { Button, Field } from '../components/ui';
import { IconShield } from '../components/icons';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await axios.post<LoginResponse>(
        (import.meta.env.VITE_API_URL || 'http://localhost:8000') +
          '/api/admin/auth/login',
        params,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );

      login(response.data.access_token);
      navigate('/dashboard');
    } catch {
      toast.error('Неверные учётные данные');
      setPassword('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center px-4 overflow-hidden bg-slate-50">
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage:
            'radial-gradient(at 20% 20%, rgba(99,102,241,0.18) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(56,189,248,0.15) 0px, transparent 50%), radial-gradient(at 70% 90%, rgba(167,139,250,0.18) 0px, transparent 50%)',
        }}
      />
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage:
            'linear-gradient(#0f172a 1px, transparent 1px), linear-gradient(90deg, #0f172a 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative w-full max-w-md animate-fade-up">
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white flex items-center justify-center shadow-[0_8px_24px_-8px_rgba(99,102,241,0.6)] mb-4">
            <IconShield width={26} height={26} />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Админ-панель
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            NN Events — модерация и управление
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-[var(--shadow-pop)] p-7">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Логин">
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                className="w-full h-11 px-3.5 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus-ring"
                placeholder="admin"
                required
              />
            </Field>
            <Field label="Пароль">
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-11 px-3.5 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus-ring"
                placeholder="••••••••"
                required
              />
            </Field>
            <Button
              type="submit"
              loading={loading}
              className="w-full !h-11"
              variant="primary"
            >
              {loading ? 'Вход…' : 'Войти'}
            </Button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          © {new Date().getFullYear()} NN Events Bot · Нижний Новгород
        </p>
      </div>
    </div>
  );
}
