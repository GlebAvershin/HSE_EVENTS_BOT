export interface Event {
  id: number;
  title: string;
  description: string | null;
  category: string;
  date_start: string;
  date_end: string | null;
  location: string | null;
  address: string | null;
  source_url: string | null;
  image_url: string | null;
  is_moderated: boolean;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface RecentEvent {
  id: number;
  title: string;
  category: string;
  date_start: string;
  is_published: boolean;
}

export interface Stats {
  events_total: number;
  events_published: number;
  events_pending: number;
  users_total: number;
  sources: SourceStatus[];
  events_by_category: CategoryCount[];
  recent_events: RecentEvent[];
}

export interface SourceStatus {
  id: number;
  name: string;
  parser_type: string;
  is_active: boolean;
  last_parsed_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Source {
  id: number;
  name: string;
  url: string | null;
  parser_type: string;
  is_active: boolean;
  last_parsed_at: string | null;
}
