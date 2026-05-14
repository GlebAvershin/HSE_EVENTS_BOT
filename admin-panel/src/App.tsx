import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import { Spinner } from './components/ui';

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const EventsPage = lazy(() => import('./pages/EventsPage'));
const SourcesPage = lazy(() => import('./pages/SourcesPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 15_000,
    },
  },
});

function PageFallback() {
  return (
    <div className="flex items-center justify-center py-20 text-slate-400">
      <Spinner size={22} />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route
              path="/dashboard"
              element={
                <Suspense fallback={<PageFallback />}>
                  <DashboardPage />
                </Suspense>
              }
            />
            <Route
              path="/events"
              element={
                <Suspense fallback={<PageFallback />}>
                  <EventsPage />
                </Suspense>
              }
            />
            <Route
              path="/sources"
              element={
                <Suspense fallback={<PageFallback />}>
                  <SourcesPage />
                </Suspense>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0f172a',
            color: '#fff',
            fontSize: '13px',
            borderRadius: '10px',
            padding: '10px 14px',
            boxShadow: '0 10px 30px -10px rgba(15,23,42,0.4)',
          },
          success: { iconTheme: { primary: '#10b981', secondary: '#fff' } },
          error: { iconTheme: { primary: '#f43f5e', secondary: '#fff' } },
        }}
      />
    </QueryClientProvider>
  );
}

export default App;
