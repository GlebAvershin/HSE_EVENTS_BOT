import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { Stats } from '../types/api';
import { Badge, Card, EmptyState, Skeleton } from '../components/ui';
import {
  IconCalendar,
  IconCheck,
  IconClock,
  IconUsers,
  IconSources,
  IconSparkle,
  IconInbox,
} from '../components/icons';
import type { ComponentType, SVGProps } from 'react';

type StatTone = 'indigo' | 'emerald' | 'amber' | 'sky';

const toneStyles: Record<
  StatTone,
  {
    bg: string;
    iconBg: string;
    iconColor: string;
    accent: string;
    valueGradient: string;
  }
> = {
  indigo: {
    bg: 'from-brand-500/[0.08] via-white to-white',
    iconBg: 'bg-gradient-to-br from-brand-500 to-brand-700',
    iconColor: 'text-white',
    accent: 'bg-brand-500',
    valueGradient: 'from-brand-700 to-brand-500',
  },
  emerald: {
    bg: 'from-emerald-500/[0.08] via-white to-white',
    iconBg: 'bg-gradient-to-br from-emerald-500 to-emerald-700',
    iconColor: 'text-white',
    accent: 'bg-emerald-500',
    valueGradient: 'from-emerald-700 to-emerald-500',
  },
  amber: {
    bg: 'from-amber-500/[0.10] via-white to-white',
    iconBg: 'bg-gradient-to-br from-amber-500 to-orange-600',
    iconColor: 'text-white',
    accent: 'bg-amber-500',
    valueGradient: 'from-amber-700 to-orange-500',
  },
  sky: {
    bg: 'from-sky-500/[0.08] via-white to-white',
    iconBg: 'bg-gradient-to-br from-sky-500 to-sky-700',
    iconColor: 'text-white',
    accent: 'bg-sky-500',
    valueGradient: 'from-sky-700 to-sky-500',
  },
};

const parserMeta: Record<
  string,
  { emoji: string; gradient: string; label: string }
> = {
  it52: { emoji: '🟦', gradient: 'from-blue-500 to-blue-700', label: 'IT52.info' },
  habr: { emoji: '🟩', gradient: 'from-emerald-500 to-emerald-700', label: 'Habr Events' },
  kudago: { emoji: '🟪', gradient: 'from-purple-500 to-purple-700', label: 'KudaGo' },
  milo: { emoji: '🟧', gradient: 'from-orange-500 to-rose-600', label: 'Milo Hall' },
  kassir: { emoji: '🟥', gradient: 'from-rose-500 to-rose-700', label: 'Kassir.ru' },
  qtickets: { emoji: '🟨', gradient: 'from-amber-500 to-yellow-600', label: 'QTickets' },
  yandex_afisha: { emoji: '🟫', gradient: 'from-yellow-500 to-amber-700', label: 'Яндекс.Афиша' },
  vk: { emoji: '🟦', gradient: 'from-sky-500 to-blue-700', label: 'ВКонтакте' },
  custom: { emoji: '⬛', gradient: 'from-slate-500 to-slate-700', label: 'Custom' },
};

const categoryMeta: Record<string, { color: string; label: string }> = {
  it: { color: '#6366f1', label: 'IT' },
  entertainment: { color: '#06b6d4', label: 'Развлечения' },
};

const fallbackPalette = ['#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899'];

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery<Stats>({
    queryKey: ['admin-stats'],
    queryFn: () => api.get('/api/admin/stats').then((r) => r.data),
    staleTime: 30_000,
  });

  const publishedRatio =
    stats && stats.events_total > 0
      ? Math.round((stats.events_published / stats.events_total) * 100)
      : 0;

  const activeSources = stats?.sources.filter((s) => s.is_active).length ?? 0;
  const sourcesTotal = stats?.sources.length ?? 0;

  return (
    <div className="space-y-7 max-w-7xl">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          tone="indigo"
          icon={IconCalendar}
          label="Всего событий"
          value={stats?.events_total}
          loading={isLoading}
          hint={`${activeSources}/${sourcesTotal} источников активны`}
        />
        <StatCard
          tone="emerald"
          icon={IconCheck}
          label="Опубликовано"
          value={stats?.events_published}
          loading={isLoading}
          hint={`${publishedRatio}% от общего числа`}
          progress={publishedRatio}
        />
        <StatCard
          tone="amber"
          icon={IconClock}
          label="На модерации"
          value={stats?.events_pending}
          loading={isLoading}
          hint="Ждут проверки"
        />
        <StatCard
          tone="sky"
          icon={IconUsers}
          label="Пользователей"
          value={stats?.users_total}
          loading={isLoading}
          hint="В Telegram-боте"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <Card className="xl:col-span-2 p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-brand-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
          <div className="relative">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-base font-semibold text-slate-900">
                  Прогресс модерации
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Соотношение опубликованных и неопубликованных событий
                </p>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold tabular-nums bg-gradient-to-br from-brand-700 to-brand-500 bg-clip-text text-transparent">
                  {publishedRatio}
                </span>
                <span className="text-xl font-semibold text-slate-300">%</span>
              </div>
            </div>

            {!isLoading && stats && (
              <>
                <div className="h-3 bg-slate-100 rounded-full overflow-hidden flex">
                  <div
                    className="h-full bg-gradient-to-r from-brand-600 via-brand-500 to-brand-400 transition-all duration-700 relative"
                    style={{ width: `${publishedRatio}%` }}
                  >
                    <div className="absolute inset-0 bg-white/20 animate-pulse" />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-5">
                  <MiniMetric
                    label="Всего"
                    value={stats.events_total}
                    color="text-slate-900"
                  />
                  <MiniMetric
                    label="Опубликовано"
                    value={stats.events_published}
                    color="text-emerald-600"
                  />
                  <MiniMetric
                    label="На модерации"
                    value={stats.events_pending}
                    color="text-amber-600"
                  />
                </div>
              </>
            )}
            {isLoading && <Skeleton height={80} />}
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                Категории
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Распределение событий
              </p>
            </div>
          </div>
          {isLoading ? (
            <div className="flex items-center justify-center py-6">
              <Skeleton height={140} width={140} className="rounded-full" />
            </div>
          ) : (
            <CategoryDonut
              data={stats?.events_by_category ?? []}
              total={stats?.events_total ?? 0}
            />
          )}
        </Card>
      </div>

      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <IconSources width={16} height={16} className="text-slate-400" />
            <h2 className="text-base font-semibold text-slate-900">
              Источники парсинга
            </h2>
          </div>
          {stats?.sources && (
            <Badge tone={activeSources === sourcesTotal ? 'green' : 'amber'}>
              {activeSources} из {sourcesTotal} активны
            </Badge>
          )}
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} height={110} />
            ))}
          </div>
        ) : !stats?.sources || stats.sources.length === 0 ? (
          <Card className="overflow-hidden">
            <EmptyState
              icon={<IconSources width={22} height={22} />}
              title="Нет подключённых источников"
              description="Добавьте источник на странице «Источники», чтобы начать сбор событий."
            />
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {stats.sources.map((source) => (
              <ParserCard
                key={source.id}
                name={source.name}
                parserType={source.parser_type}
                isActive={source.is_active}
                lastParsedAt={source.last_parsed_at}
              />
            ))}
          </div>
        )}
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <Card className="xl:col-span-2 overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                Последние события
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Недавно добавленные парсерами
              </p>
            </div>
            <a
              href="/events"
              className="text-xs font-medium text-brand-600 hover:text-brand-700"
            >
              Все события →
            </a>
          </div>
          {isLoading ? (
            <div className="p-5 space-y-3">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} height={56} />
              ))}
            </div>
          ) : !stats?.recent_events || stats.recent_events.length === 0 ? (
            <EmptyState
              icon={<IconInbox width={22} height={22} />}
              title="Нет событий"
              description="События появятся после следующего запуска парсеров."
            />
          ) : (
            <ul className="divide-y divide-slate-100">
              {stats.recent_events.map((e) => {
                const cat = categoryMeta[e.category];
                return (
                  <li
                    key={e.id}
                    className="px-6 py-3.5 flex items-center gap-4 hover:bg-slate-50/60 transition-colors"
                  >
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center text-white shrink-0 shadow-sm"
                      style={{
                        background:
                          cat?.color ??
                          fallbackPalette[e.id % fallbackPalette.length],
                      }}
                    >
                      <IconCalendar width={18} height={18} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-slate-900 truncate">
                        {e.title}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                        <span>{cat?.label ?? e.category}</span>
                        <span className="text-slate-300">·</span>
                        <span>
                          {new Date(e.date_start).toLocaleDateString('ru-RU', {
                            day: '2-digit',
                            month: 'short',
                          })}
                        </span>
                      </div>
                    </div>
                    {e.is_published ? (
                      <Badge tone="green">Опубликовано</Badge>
                    ) : (
                      <Badge tone="amber">На модерации</Badge>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <Card className="p-6 bg-gradient-to-br from-slate-900 via-slate-800 to-brand-900 text-white relative overflow-hidden">
          <div className="absolute -top-8 -right-8 w-40 h-40 bg-brand-500/30 rounded-full blur-3xl" />
          <div className="absolute -bottom-12 -left-12 w-44 h-44 bg-purple-500/20 rounded-full blur-3xl" />
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center mb-4">
              <IconSparkle width={20} height={20} className="text-amber-300" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Автоматический парсинг</h3>
            <p className="text-sm text-slate-300 leading-relaxed mb-5">
              Парсеры запускаются каждые 12 часов. Прошедшие события удаляются ежедневно в&nbsp;03:00.
            </p>

            <div className="space-y-2.5 text-sm">
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>Расписание: каждые 12 часов</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span>Очистка прошлых: 03:00 ежедневно</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
                <span>Дедупликация по source_url</span>
              </div>
            </div>

            <div className="mt-5 pt-5 border-t border-white/10">
              <p className="text-xs text-slate-400 mb-2">Запустить вручную:</p>
              <code className="block text-xs bg-black/30 border border-white/10 px-3 py-2 rounded-lg text-amber-300 font-mono">
                /admin_parse
              </code>
              <p className="text-[11px] text-slate-500 mt-2">
                Отправьте боту в Telegram
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

interface StatCardProps {
  tone: StatTone;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  label: string;
  value: number | undefined;
  loading: boolean;
  hint?: string;
  progress?: number;
}

function StatCard({
  tone,
  icon: Icon,
  label,
  value,
  loading,
  hint,
  progress,
}: StatCardProps) {
  const t = toneStyles[tone];
  return (
    <div className="relative bg-white rounded-2xl border border-slate-200/80 shadow-[var(--shadow-card)] p-5 overflow-hidden group hover:shadow-[var(--shadow-pop)] transition-shadow">
      <div className={`absolute inset-0 bg-gradient-to-br ${t.bg} pointer-events-none`} />
      <div className={`absolute top-0 left-0 right-0 h-1 ${t.accent}`} />
      <div className="relative flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            {label}
          </div>
          <div
            className={`mt-2 text-3xl font-bold tabular-nums bg-gradient-to-br ${t.valueGradient} bg-clip-text text-transparent`}
          >
            {loading ? (
              <Skeleton height={32} width={64} />
            ) : (
              (value ?? 0).toLocaleString('ru-RU')
            )}
          </div>
          {hint && !loading && (
            <div className="text-xs text-slate-500 mt-1.5">{hint}</div>
          )}
          {typeof progress === 'number' && !loading && (
            <div className="mt-3 h-1 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${t.accent} rounded-full transition-all duration-700`}
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>
        <div
          className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${t.iconBg} shadow-md group-hover:scale-110 transition-transform`}
        >
          <Icon width={20} height={20} className={t.iconColor} />
        </div>
      </div>
    </div>
  );
}

function MiniMetric({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${color}`}>
        {value.toLocaleString('ru-RU')}
      </div>
    </div>
  );
}

function CategoryDonut({
  data,
  total,
}: {
  data: { category: string; count: number }[];
  total: number;
}) {
  if (data.length === 0 || total === 0) {
    return (
      <div className="text-center py-6 text-sm text-slate-400">Нет данных</div>
    );
  }

  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  const slices = data.map((d, idx) => {
    const meta = categoryMeta[d.category];
    const color = meta?.color ?? fallbackPalette[idx % fallbackPalette.length];
    const ratio = d.count / total;
    const dash = ratio * circumference;
    const slice = {
      color,
      label: meta?.label ?? d.category,
      count: d.count,
      ratio,
      dash,
      offset,
    };
    offset += dash;
    return slice;
  });

  return (
    <div className="flex items-center gap-5">
      <div className="relative shrink-0">
        <svg width="140" height="140" viewBox="0 0 140 140">
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke="#f1f5f9"
            strokeWidth="16"
          />
          {slices.map((s, i) => (
            <circle
              key={i}
              cx="70"
              cy="70"
              r={radius}
              fill="none"
              stroke={s.color}
              strokeWidth="16"
              strokeDasharray={`${s.dash} ${circumference - s.dash}`}
              strokeDashoffset={-s.offset}
              transform="rotate(-90 70 70)"
              strokeLinecap="butt"
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-slate-900 tabular-nums leading-none">
            {total}
          </span>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 mt-1">
            событий
          </span>
        </div>
      </div>

      <ul className="flex-1 space-y-2.5 min-w-0">
        {slices.map((s, i) => (
          <li key={i} className="flex items-center gap-2.5">
            <span
              className="w-3 h-3 rounded-sm shrink-0"
              style={{ background: s.color }}
            />
            <span className="text-sm text-slate-700 truncate flex-1">
              {s.label}
            </span>
            <span className="text-sm font-semibold text-slate-900 tabular-nums">
              {s.count}
            </span>
            <span className="text-xs text-slate-400 tabular-nums w-9 text-right">
              {Math.round(s.ratio * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ParserCard({
  name,
  parserType,
  isActive,
  lastParsedAt,
}: {
  name: string;
  parserType: string;
  isActive: boolean;
  lastParsedAt: string | null;
}) {
  const meta = parserMeta[parserType] ?? parserMeta.custom;
  return (
    <div className="relative bg-white rounded-2xl border border-slate-200/80 shadow-[var(--shadow-card)] p-5 overflow-hidden group hover:shadow-[var(--shadow-pop)] hover:-translate-y-0.5 transition-all">
      <div
        className={`absolute -top-12 -right-12 w-32 h-32 bg-gradient-to-br ${meta.gradient} opacity-10 rounded-full blur-2xl`}
      />
      <div className="relative">
        <div className="flex items-start justify-between mb-3">
          <div
            className={`w-11 h-11 rounded-xl bg-gradient-to-br ${meta.gradient} flex items-center justify-center text-white shadow-md`}
          >
            <IconSources width={20} height={20} />
          </div>
          <Badge tone={isActive ? 'green' : 'gray'}>
            {isActive ? 'Активен' : 'Выкл.'}
          </Badge>
        </div>
        <h3 className="text-base font-semibold text-slate-900 mb-1 truncate">
          {name}
        </h3>
        <code className="inline-block text-[11px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded mb-3">
          {parserType}
        </code>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <IconClock width={12} height={12} />
          <span>
            {lastParsedAt ? (
              formatRelative(lastParsedAt)
            ) : (
              <span className="text-slate-400">ещё не парсилось</span>
            )}
          </span>
        </div>
      </div>
    </div>
  );
}

function formatRelative(iso: string): string {
  const d = new Date(iso);
  const diffMin = Math.floor((Date.now() - d.getTime()) / 60_000);
  if (diffMin < 1) return 'только что';
  if (diffMin < 60) return `${diffMin} мин назад`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH} ч назад`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 7) return `${diffD} дн назад`;
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}
