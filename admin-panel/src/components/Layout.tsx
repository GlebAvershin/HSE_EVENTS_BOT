import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import {
  IconDashboard,
  IconCalendar,
  IconSources,
  IconLogout,
  IconShield,
} from './icons';
import type { ComponentType, SVGProps } from 'react';

interface NavItem {
  to: string;
  label: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
}

const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Панель', icon: IconDashboard },
  { to: '/events', label: 'События', icon: IconCalendar },
  { to: '/sources', label: 'Источники', icon: IconSources },
];

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': {
    title: 'Панель управления',
    subtitle: 'Сводная статистика и состояние парсеров',
  },
  '/events': {
    title: 'Модерация событий',
    subtitle: 'Публикация, редактирование и удаление событий',
  },
  '/sources': {
    title: 'Источники',
    subtitle: 'Управление парсерами и подключёнными источниками',
  },
};

export default function Layout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();
  const meta = pageTitles[location.pathname] ?? {
    title: 'NN Events',
    subtitle: '',
  };

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="flex min-h-screen text-slate-900">
      {/* Фоновые декоративные элементы */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-brand-400/20 to-purple-400/20 rounded-full blur-3xl animate-float" />
        <div className="absolute top-1/2 -left-20 w-72 h-72 bg-gradient-to-br from-emerald-400/15 to-cyan-400/15 rounded-full blur-3xl animate-float-delayed" />
        <div className="absolute -bottom-20 right-1/3 w-80 h-80 bg-gradient-to-br from-amber-400/10 to-rose-400/10 rounded-full blur-3xl animate-float" />
      </div>

      <aside className="w-64 shrink-0 flex flex-col sticky top-0 h-screen glass-dark">
        <div className="px-5 py-5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-400 via-brand-500 to-purple-600 text-white flex items-center justify-center shadow-[0_4px_16px_-2px_rgba(99,102,241,0.5)] animate-gradient">
            <IconShield width={20} height={20} />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-bold text-white">NN Events</div>
            <div className="text-[11px] text-brand-300 uppercase tracking-wider font-medium">
              Admin Panel
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 mt-2">
          <div className="px-2 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Меню
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium mb-1 transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-brand-500/20 to-purple-500/10 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]'
                      : 'text-slate-400 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      width={18}
                      height={18}
                      className={
                        isActive
                          ? 'text-brand-300'
                          : 'text-slate-500 group-hover:text-slate-300'
                      }
                    />
                    <span>{item.label}</span>
                    {isActive && (
                      <span className="ml-auto w-2 h-2 rounded-full bg-brand-400 animate-pulse-dot" />
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        <div className="p-3 border-t border-white/10">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-400 to-purple-500 text-white flex items-center justify-center text-sm font-bold shadow-md">
              C
            </div>
            <div className="flex-1 min-w-0 leading-tight">
              <div className="text-sm font-medium text-white truncate">
                CEOGlebik
              </div>
              <div className="text-xs text-slate-400 truncate">
                Полный доступ
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 p-2 rounded-lg transition-colors focus-ring"
              title="Выйти"
              aria-label="Выйти"
            >
              <IconLogout width={16} height={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-10 glass border-b border-white/40">
          <div className="px-8 py-5">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              {meta.title}
            </h1>
            {meta.subtitle && (
              <p className="text-sm text-slate-500 mt-0.5">{meta.subtitle}</p>
            )}
          </div>
        </header>
        <div className="flex-1 px-8 py-6 animate-fade-up">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
