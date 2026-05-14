import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '../api/client';
import type { Source } from '../types/api';
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
  IconPlus,
  IconEdit,
  IconTrash,
  IconSources,
  IconExternal,
} from '../components/icons';

const parserTypeLabels: Record<string, string> = {
  yandex_afisha: 'Яндекс.Афиша',
  vk: 'ВКонтакте',
  it52: 'IT52',
  habr: 'Habr Events',
  kudago: 'KudaGo',
  milo: 'Milo',
  kassir: 'Kassir.ru',
  qtickets: 'QTickets',
  custom: 'Другой',
};

export default function SourcesPage() {
  const queryClient = useQueryClient();
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [showForm, setShowForm] = useState(false);

  const { data: sources, isLoading } = useQuery<Source[]>({
    queryKey: ['admin-sources'],
    queryFn: () => api.get('/api/admin/sources').then((r) => r.data),
    staleTime: 30_000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/admin/sources/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-sources'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      toast.success('Источник удалён');
    },
    onError: () => toast.error('Ошибка удаления'),
  });

  const handleDelete = (source: Source) => {
    if (confirm(`Удалить источник «${source.name}»?`)) {
      deleteMutation.mutate(source.id);
    }
  };

  const openCreate = () => {
    setEditingSource(null);
    setShowForm(true);
  };

  const openEdit = (source: Source) => {
    setEditingSource(source);
    setShowForm(true);
  };

  return (
    <div className="space-y-5 max-w-7xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          {sources && !isLoading
            ? `Всего источников: ${sources.length}`
            : 'Загрузка списка…'}
        </p>
        <Button onClick={openCreate} icon={<IconPlus width={15} height={15} />}>
          Добавить источник
        </Button>
      </div>

      <Card className="overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} height={48} />
            ))}
          </div>
        ) : !sources || sources.length === 0 ? (
          <EmptyState
            icon={<IconSources width={24} height={24} />}
            title="Нет источников"
            description="Добавьте первый источник, чтобы запустить парсинг событий."
            action={
              <Button onClick={openCreate} icon={<IconPlus width={15} height={15} />}>
                Добавить источник
              </Button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-50/50 border-b border-slate-100">
                  <th className="px-5 py-3">Источник</th>
                  <th className="px-5 py-3">Тип парсера</th>
                  <th className="px-5 py-3">Статус</th>
                  <th className="px-5 py-3">Последний парсинг</th>
                  <th className="px-5 py-3 text-right">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sources.map((source) => (
                  <tr
                    key={source.id}
                    className="hover:bg-slate-50/60 transition-colors"
                  >
                    <td className="px-5 py-3.5">
                      <div className="text-sm font-medium text-slate-900">
                        {source.name}
                      </div>
                      {source.url && (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-brand-600 mt-0.5 max-w-xs truncate"
                        >
                          <span className="truncate">{source.url}</span>
                          <IconExternal width={11} height={11} className="shrink-0" />
                        </a>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <code className="text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                        {parserTypeLabels[source.parser_type] ?? source.parser_type}
                      </code>
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge tone={source.is_active ? 'green' : 'gray'}>
                        {source.is_active ? 'Активен' : 'Неактивен'}
                      </Badge>
                    </td>
                    <td className="px-5 py-3.5 text-sm text-slate-600 tabular-nums whitespace-nowrap">
                      {source.last_parsed_at ? (
                        new Date(source.last_parsed_at).toLocaleString('ru-RU', {
                          day: '2-digit',
                          month: 'short',
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      ) : (
                        <span className="text-slate-400">— ещё не парсилось</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5 justify-end">
                        <button
                          onClick={() => openEdit(source)}
                          className="inline-flex items-center justify-center w-8 h-8 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors focus-ring"
                          title="Редактировать"
                          aria-label="Редактировать"
                        >
                          <IconEdit width={15} height={15} />
                        </button>
                        <button
                          onClick={() => handleDelete(source)}
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

      <Modal
        open={showForm}
        onClose={() => setShowForm(false)}
        title={editingSource ? 'Редактировать источник' : 'Новый источник'}
      >
        <SourceForm
          source={editingSource}
          onClose={() => setShowForm(false)}
        />
      </Modal>
    </div>
  );
}

function SourceForm({
  source,
  onClose,
}: {
  source: Source | null;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(source?.name ?? '');
  const [url, setUrl] = useState(source?.url ?? '');
  const [parserType, setParserType] = useState(source?.parser_type ?? 'custom');
  const [isActive, setIsActive] = useState(source?.is_active ?? true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        name,
        url: url || null,
        parser_type: parserType,
        is_active: isActive,
      };

      if (source) {
        await api.patch(`/api/admin/sources/${source.id}`, payload);
        toast.success('Источник обновлён');
      } else {
        await api.post('/api/admin/sources', payload);
        toast.success('Источник создан');
      }

      queryClient.invalidateQueries({ queryKey: ['admin-sources'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      onClose();
    } catch {
      toast.error('Ошибка сохранения');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Название">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring"
          placeholder="Например, IT52.info"
          autoFocus
          required
        />
      </Field>

      <Field label="URL" hint="Необязательно — основная страница или фид источника">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 text-slate-900 focus-ring"
          placeholder="https://example.com"
        />
      </Field>

      <Field label="Тип парсера">
        <select
          value={parserType}
          onChange={(e) => setParserType(e.target.value)}
          className="w-full h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 focus-ring appearance-none bg-no-repeat bg-right pr-9"
          style={{
            backgroundImage:
              "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='m6 9 6 6 6-6'/></svg>\")",
            backgroundSize: '16px 16px',
            backgroundPosition: 'right 10px center',
          }}
        >
          <option value="yandex_afisha">Яндекс.Афиша</option>
          <option value="vk">ВКонтакте</option>
          <option value="it52">IT52</option>
          <option value="habr">Habr Events</option>
          <option value="kudago">KudaGo</option>
          <option value="milo">Milo</option>
          <option value="kassir">Kassir.ru</option>
          <option value="qtickets">QTickets</option>
          <option value="custom">Другой</option>
        </select>
      </Field>

      <label className="flex items-center justify-between p-3 bg-slate-50 rounded-lg cursor-pointer">
        <div>
          <div className="text-sm font-medium text-slate-900">Активен</div>
          <div className="text-xs text-slate-500 mt-0.5">
            Источник будет участвовать в автоматическом парсинге
          </div>
        </div>
        <Toggle checked={isActive} onChange={setIsActive} />
      </label>

      <div className="flex items-center justify-end gap-2 pt-2">
        <Button type="button" variant="secondary" onClick={onClose}>
          Отмена
        </Button>
        <Button type="submit" loading={loading}>
          {source ? 'Сохранить' : 'Создать'}
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
