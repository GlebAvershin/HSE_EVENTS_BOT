import { create } from 'zustand';

interface AuthState {
  accessToken: string | null;
  login: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  login: (token: string) => set({ accessToken: token }),
  logout: () => set({ accessToken: null }),
}));
