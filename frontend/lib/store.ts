import { create } from 'zustand';

interface AuthStore {
  user: any;
  isLoggedIn: boolean;
  setUser: (user: any) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isLoggedIn: false,
  setUser: (user) => set({ user, isLoggedIn: !!user }),
  logout: () => set({ user: null, isLoggedIn: false }),
}));

interface SearchStore {
  fromLocation: string;
  toLocation: string;
  pickupDate: string;
  dropoffDate?: string;
  passengers: number;
  setSearchParams: (params: Partial<SearchStore>) => void;
}

export const useSearchStore = create<SearchStore>((set) => ({
  fromLocation: '',
  toLocation: '',
  pickupDate: '',
  dropoffDate: '',
  passengers: 1,
  setSearchParams: (params) => set(params),
}));

interface UIStore {
  language: 'en' | 'hi';
  toggleLanguage: () => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  language: 'hi',
  toggleLanguage: () => set((state) => ({ language: state.language === 'en' ? 'hi' : 'en' })),
  sidebarOpen: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
