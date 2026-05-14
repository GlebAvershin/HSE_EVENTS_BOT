import { useState } from 'react';
import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '../api/client';
import type { Event, PaginatedResponse } from '../types/api';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  Modal,
  Skeleton,
} from '../components/ui';
import {
  IconSearch,
  IconCheck,
  IconTrash,
  IconChevronLeft,
  IconChevronRight,
  IconExternal,
  IconInbox,
  IconEdit,
  IconPlus,
} from '../components/icons';
import { useDebouncedValue } from '../hooks/useDebouncedValue';

type StatusFilter = 'all' | 'pending' | 'published';
type CategoryFilter = 'all' | 'it' | 'entertainment';

const statusTabs: { label: string; value: StatusFilter }[] = [
  { label: 'Все', value: 'all' },
  { label: 'На модерации', value: 'pending' },
  { label: 'Опубликованные', value: 'published' },
];

const categoryTabs: { label: string; value: CategoryFilter }[] = [
  { label: 'Все категории', value: 'all' },
  { label: 'IT', value: 'it' },
  { label: 'Развлечения', value: 'entertainment' },
];

export default function EventsPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<StatusFilter>('all');
  const [category, setCategory] = useState<CategoryFilter>('all');
  const [searchInput, setSearchInput] = useState('');
  const search = useDebouncedValue(searchInput, 350);
  const [editing, setEditing] = useState<Event | null>(null);
  const [creating, setCreating] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, isFetching } = useQuery<PaginatedResponse<Event>>({
    queryKey: ['admin-events', page, status, category, search],
    queryFn: () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', '20');
      if (status !== 'all') params.set('status', status);
      if (category !== 'all') params.set('category', category);
      if (search) params.set('search', search);
      return api.get(`/api/admin/events?${params}`).then((r) => r.data);
    },
    placeholderData: keepPreviousData,
    staleTime: 10_000,
  });

  const publishMutation = useMutation({
    mutationFn: (eventId: number) => api.post(`/api/admin/events/${eventId}/publish`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-events'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      toast.success('Событие опубликовано');
    },
    onError: () => toast.error('Ошибка публикации'),
  });

  const deleteMutation = useMutation({
    mutationFn: (eventId: number) => api.delete(`/api/admin/events/${eventId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-events'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      toast.success('Событие удалено');
    },
    onError: () => toast.error('Ошибка удаления'),
  });

  const handleDelete = (event: Event) => {
    if (confirm(`Удалить событие «${event.title}»?`)) {
      deleteMutation.mutate(event.id);
    }
  };

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 0;
  const showSkeleton = isLoading && !data;

  return (
    <div className="space-y-5 max-w-7xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          {data ? `Найдено событий: ${data.total}` : 'Загрузка…'}
        </p>
        <Button
          icon={<IconPlus width={15} height={15} />}
          onClick={() => setCreating(true)}
        >
          Создать событие
        </Button>
      </div>

      <Card className="p-4">
        <div className="flex flex-col xl:flex-row gap-3 xl:items-center xl:justify-between">
          <div className="flex flex-wrap gap-2">
            <FilterTabs
              tabs={statusTabs}
              value={status}
              onChange={(v) => {
                setStatus(v);
                setPage(1);
              }}
              dark
            />
            <FilterTabs
              tabs={categoryTabs}
              value={category}
              onChange={(v) => {
                setCategory(v);
                setPage(1);
              }}
            />
          </div>

          <div className="relative w-full xl:w-80">
            <IconSearch
              width={16}
              height={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
            />
            <input
              type="text"
              placeholder="Поиск по названию или описанию…"
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value);
                setPage(1);
              }}
              className="w-full h-10 pl-9 pr-9 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring"
            />
            {searchInput && (
              <button
                onClick={() => setSearchInput('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 p-1 rounded"
                aria-label="Очистить"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </Card>

      <Card className="overflow-hidden relative">
        {isFetching && !showSkeleton && (
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-brand-100 overflow-hidden">
            <div className="h-full w-1/3 bg-brand-500 animate-[shimmer_1s_ease-in-out_infinite]" />
          </div>
        )}

        {showSkeleton ? (
          <div className="p-6 space-y-3">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} height={48} />
            ))}
          </div>
        ) : !data?.items || data.items.length === 0 ? (
          <EmptyState
            icon={<IconInbox width={24} height={24} />}
            title={search ? 'Ничего не найдено' : 'Нет событий'}
            description={
              search
                ? 'Попробуйте изменить запрос или сбросить фильтры.'
                : 'События появятся после следующего запуска парсеров.'
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-50/50 border-b border-slate-100">
                  <th className="px-5 py-3">Событие</th>
                  <th className="px-5 py-3">Категория</th>
                  <th className="px-5 py-3">Дата</th>
                  <th className="px-5 py-3">Статус</th>
                  <th className="px-5 py-3 text-right">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((event) => (
                  <tr
                    key={event.id}
                    className="hover:bg-slate-50/60 transition-colors group"
                  >
                    <td className="px-5 py-3.5 max-w-md">
                      <div className="flex items-start gap-3">
                        {event.image_url ? (
                          <img
                            src={event.image_url}
                            alt=""
                            loading="lazy"
                            className="w-10 h-10 rounded-lg object-cover bg-slate-100 shrink-0"
                            onError={(e) => {
                              (e.currentTarget as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        ) : (
                          <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-400 flex items-center justify-center shrink-0">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                              <rect x="3" y="3" width="18" height="18" rx="2" />
                              <circle cx="8.5" cy="8.5" r="1.5" />
                              <path d="m21 15-5-5L5 21" />
                            </svg>
                          </div>
                        )}
                        <div className="min-w-0">
                          <div className="text-sm font-medium text-slate-900 truncate">
                            {event.title}
                          </div>
                          {event.location && (
                            <div className="text-xs text-slate-500 truncate mt-0.5">
                              {event.location}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <CategoryBadge category={event.category} />
                    </td>
                    <td className="px-5 py-3.5 text-sm text-slate-600 tabular-nums whitespace-nowrap">
                      {new Date(event.date_start).toLocaleDateString('ru-RU', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="px-5 py-3.5">
                      {event.is_published ? (
                        <Badge tone="green">Опубликовано</Badge>
                      ) : (
                        <Badge tone="amber">На модерации</Badge>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5 justify-end">
                        {event.source_url && (
                          <a
                            href={event.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center justify-center w-8 h-8 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors"
                            title="Открыть источник"
                          >
                            <IconExternal width={15} height={15} />
                          </a>
                        )}
                        <button
                          onClick={() => setEditing(event)}
                          className="inline-flex items-center justify-center w-8 h-8 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors focus-ring"
                          title="Редактировать"
                          aria-label="Редактировать"
                        >
                          <IconEdit width={15} height={15} />
                        </button>
                        {!event.is_published && (
                          <Button
                            size="sm"
                            variant="success"
                            icon={<IconCheck width={13} height={13} />}
                            onClick={() => publishMutation.mutate(event.id)}
                            loading={
                              publishMutation.isPending &&
                              publishMutation.variables === event.id
                            }
                          >
                            Опубликовать
                          </Button>
                        )}
                        <button
                          onClick={() => handleDelete(event)}
                          className="inline-flex items-center justify-center w-8 h-8 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors focus-ring"
                          title="Удалить"
                          aria-label="Удалить"
                        >
                          <IconTrash width={15} height={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {data && totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-500">
            Страница{' '}
            <span className="font-medium text-slate-900 tabular-nums">{data.page}</span>{' '}
            из{' '}
            <span className="font-medium text-slate-900 tabular-nums">{totalPages}</span>{' '}
            <span className="text-slate-400">·</span> всего:{' '}
            <span className="font-medium text-slate-900 tabular-nums">{data.total}</span>
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              icon={<IconChevronLeft width={14} height={14} />}
            >
              Назад
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Вперёд <IconChevronRight width={14} height={14} />
            </Button>
          </div>
        </div>
      )}

      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title="Редактировать событие"
        size="lg"
      >
        {editing && (
          <EventForm
            event={editing}
            onClose={() => setEditing(null)}
          />
        )}
      </Modal>

      <Modal
        open={creating}
        onClose={() => setCreating(false)}
        title="Создать событие"
        size="lg"
      >
        {creating && (
          <EventForm
            event={null}
            onClose={() => setCreating(false)}
          />
        )}
      </Modal>
    </div>
  );
}

function FilterTabs<T extends string>({
  tabs,
  value,
  onChange,
  dark,
}: {
  tabs: { label: string; value: T }[];
  value: T;
  onChange: (v: T) => void;
  dark?: boolean;
}) {
  return (
    <div className="inline-flex bg-slate-100 rounded-lg p-1">
      {tabs.map((t) => {
        const active = value === t.value;
        return (
          <button
            key={t.value}
            onClick={() => onChange(t.value)}
            className={`px-3 py-1.5 text-sm rounded-md font-medium transition-all focus-ring ${
              active
                ? dark
                  ? 'bg-slate-900 text-white shadow-[0_2px_6px_-2px_rgba(15,23,42,0.3)]'
                  : 'bg-white text-slate-900 shadow-[var(--shadow-soft)]'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}

function CategoryBadge({ category }: { category: string }) {
  const map: Record<string, { tone: 'indigo' | 'blue' | 'gray'; label: string }> = {
    it: { tone: 'indigo', label: 'IT' },
    entertainment: { tone: 'blue', label: 'Развлечения' },
  };
  const m = map[category] ?? { tone: 'gray' as const, label: category };
  return <Badge tone={m.tone}>{m.label}</Badge>;
}

interface EventFormProps {
  event: Event | null;
  onClose: () => void;
}

function toLocalInput(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  const tzOffset = d.getTimezoneOffset() * 60_000;
  return new Date(d.getTime() - tzOffset).toISOString().slice(0, 16);
}

function fromLocalInput(s: string): string | null {
  if (!s) return null;
  return new Date(s).toISOString();
}

function EventForm({ event, onClose }: EventFormProps) {
  const queryClient = useQueryClient();
  const isEdit = event !== null;
  const [title, setTitle] = useState(event?.title ?? '');
  const [description, setDescription] = useState(event?.description ?? '');
  const [category, setCategory] = useState(event?.category ?? 'it');
  const [dateStart, setDateStart] = useState(
    toLocalInput(event?.date_start ?? null)
  );
  const [dateEnd, setDateEnd] = useState(toLocalInput(event?.date_end ?? null));
  const [location, setLocation] = useState(event?.location ?? '');
  const [address, setAddress] = useState(event?.address ?? '');
  const [imageUrl, setImageUrl] = useState(event?.image_url ?? '');
  const [sourceUrl, setSourceUrl] = useState(event?.source_url ?? '');
  const [isPublished, setIsPublished] = useState(event?.is_published ?? false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const startIso = fromLocalInput(dateStart);
      if (!startIso) {
        toast.error('Укажите дату начала');
        setLoading(false);
        return;
      }
      const basePayload = {
        title,
        description: description || null,
        category,
        date_start: startIso,
        date_end: fromLocalInput(dateEnd),
        location: location || null,
        address: address || null,
        image_url: imageUrl || null,
        source_url: sourceUrl || null,
        is_published: isPublished,
      };

      if (isEdit && event) {
        await api.patch(`/api/admin/events/${event.id}`, {
          ...basePayload,
          is_moderated: isPublished ? true : event.is_moderated,
        });
        toast.success('Событие обновлено');
      } else {
        await api.post('/api/admin/events/', basePayload);
        toast.success('Событие создано');
      }

      queryClient.invalidateQueries({ queryKey: ['admin-events'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      onClose();
    } catch {
      toast.error('Ошибка сохранения');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
      <Field label="Название">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring"
          required
        />
      </Field>

      <Field label="Описание">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring resize-y"
        />
      </Field>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Категория">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 focus-ring appearance-none pr-9"
            style={{
              backgroundImage:
                "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='m6 9 6 6 6-6'/></svg>\")",
              backgroundRepeat: 'no-repeat',
              backgroundSize: '16px 16px',
              backgroundPosition: 'right 10px center',
            }}
          >
            <option value="it">IT</option>
            <option value="entertainment">Развлечения</option>
          </select>
        </Field>

        <Field label="Статус">
          <label className="flex items-center justify-between h-10 px-3 bg-slate-50 rounded-lg cursor-pointer">
            <span className="text-sm text-slate-700">
              {isPublished ? 'Опубликовано' : 'На модерации'}
            </span>
            <Toggle checked={isPublished} onChange={setIsPublished} />
          </label>
        </Field>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Начало">
          <input
            type="datetime-local"
            value={dateStart}
            onChange={(e) => setDateStart(e.target.value)}
            className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 focus-ring"
            required
          />
        </Field>
        <Field label="Окончание" hint="Опционально">
          <input
            type="datetime-local"
            value={dateEnd}
            onChange={(e) => setDateEnd(e.target.value)}
            className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 focus-ring"
          />
        </Field>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Место">
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring"
            placeholder="Название площадки"
          />
        </Field>
        <Field label="Адрес">
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring"
            placeholder="ул. ..."
          />
        </Field>
      </div>

      <Field label="Ссылка на изображение">
        <input
          type="url"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring"
          placeholder="https://…"
        />
      </Field>

      <Field label="Ссылка на источник">
        <input
          type="url"
          value={sourceUrl}
          onChange={(e) => setSourceUrl(e.target.value)}
          className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring"
          placeholder="https://…"
        />
      </Field>

      <div className="flex items-center justify-end gap-2 pt-2 sticky bottom-0 bg-white">
        <Button type="button" variant="secondary" onClick={onClose}>
          Отмена
        </Button>
        <Button type="submit" loading={loading}>
          {isEdit ? 'Сохранить' : 'Создать'}
        </Button>
      </div>
    </form>
  );
}

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-ring ${
        checked ? 'bg-brand-600' : 'bg-slate-300'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}
