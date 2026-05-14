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
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <aside className="w-64 shrink-0 bg-white border-r border-slate-200 flex flex-col sticky top-0 h-screen">
        <div className="px-5 py-5 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white flex items-center justify-center shadow-[0_4px_12px_-2px_rgba(99,102,241,0.4)]">
            <IconShield width={18} height={18} />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold text-slate-900">NN Events</div>
            <div className="text-[11px] text-slate-500 uppercase tracking-wider">
              Admin
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
                  `group flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium mb-1 transition-all ${
                    isActive
                      ? 'bg-brand-50 text-brand-700'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
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
                          ? 'text-brand-600'
                          : 'text-slate-400 group-hover:text-slate-600'
                      }
                    />
                    <span>{item.label}</span>
                    {isActive && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-500" />
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        <div className="p-3 border-t border-slate-100">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-200 to-slate-300 text-slate-700 flex items-center justify-center text-sm font-semibold">
              A
            </div>
            <div className="flex-1 min-w-0 leading-tight">
              <div className="text-sm font-medium text-slate-900 truncate">
                Администратор
              </div>
              <div className="text-xs text-slate-500 truncate">
                Полный доступ
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="text-slate-400 hover:text-rose-600 hover:bg-rose-50 p-2 rounded-lg transition-colors focus-ring"
              title="Выйти"
              aria-label="Выйти"
            >
              <IconLogout width={16} height={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-slate-200/80">
          <div className="px-8 py-5">
            <h1 className="text-xl font-semibold text-slate-900 tracking-tight">
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
