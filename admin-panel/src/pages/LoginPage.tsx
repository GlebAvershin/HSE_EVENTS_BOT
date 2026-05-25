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
    <div className="min-h-screen relative flex items-center justify-center px-4 overflow-hidden bg-gradient-to-br from-slate-900 via-brand-900 to-purple-900">
      {/* Animated background orbs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/30 rounded-full blur-[100px] animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/25 rounded-full blur-[80px] animate-float-delayed" />
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-cyan-500/20 rounded-full blur-[60px] animate-float" />
      </div>
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative w-full max-w-md animate-fade-up">
        <div className="flex flex-col items-center mb-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-400 via-brand-500 to-purple-600 text-white flex items-center justify-center shadow-[0_8px_32px_-8px_rgba(99,102,241,0.7)] mb-4 animate-gradient">
            <IconShield width={30} height={30} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Админ-панель
          </h1>
          <p className="text-sm text-slate-300 mt-1">
            NN Events — модерация и управление
          </p>
        </div>

        <div className="glass-dark rounded-2xl shadow-[0_20px_60px_-15px_rgba(0,0,0,0.5)] p-7">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Логин">
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                className="w-full h-11 px-3.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus-ring"
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
                className="w-full h-11 px-3.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus-ring"
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

        <p className="text-center text-xs text-slate-500 mt-6">
          © {new Date().getFullYear()} NN Events Bot · Нижний Новгород
        </p>
      </div>
    </div>
  );
}
