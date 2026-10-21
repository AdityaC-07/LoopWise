import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Tour, useTour } from './components/Tour';
import LandingPage from './pages/LandingPage';
import ClassifyPage from './pages/ClassifyPage';
import ResultPage from './pages/ResultPage';
import AnalyticsOverviewPage from './pages/AnalyticsOverviewPage';
import WardDetailPage from './pages/WardDetailPage';
import MaterialsPage from './pages/MaterialsPage';
import HelpPage from './pages/HelpPage';
import { getHealth } from './api/client';
import type { ClassifierStatus } from './components/ServiceStatusIndicator';

/** App chrome (topbar + sidebar/tabbar) wrapping all dashboard/classify routes. */
function AppShell() {
  const { showTour, closeTour } = useTour();
  const [classifierStatus, setClassifierStatus] = useState<ClassifierStatus>('unknown');

  useEffect(() => {
    getHealth()
      .then((response) => {
        setClassifierStatus(
          response.data.components?.inference_engine === 'ok' ? 'ready' : 'unavailable'
        );
      })
      .catch(() => setClassifierStatus('unknown'));
  }, []);

  return (
    <>
      {showTour && <Tour onClose={closeTour} />}
      <Layout classifierStatus={classifierStatus}>
        <Outlet />
      </Layout>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public landing page — no app chrome */}
        <Route path="/" element={<LandingPage />} />

        {/* Main application — dashboard, classify flow, materials, help */}
        <Route element={<AppShell />}>
          <Route path="/classify" element={<ClassifyPage />} />
          <Route path="/result/:eventId" element={<ResultPage />} />
          <Route path="/analytics" element={<AnalyticsOverviewPage />} />
          <Route path="/analytics/ward/:wardId" element={<WardDetailPage />} />
          <Route path="/materials" element={<MaterialsPage />} />
          <Route path="/help" element={<HelpPage />} />
        </Route>

        {/* Fallback → landing */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
