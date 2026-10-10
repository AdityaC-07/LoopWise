import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Tour, useTour } from './components/Tour';
import ClassifyPage from './pages/ClassifyPage';
import ResultPage from './pages/ResultPage';
import AnalyticsOverviewPage from './pages/AnalyticsOverviewPage';
import WardDetailPage from './pages/WardDetailPage';
import MaterialsPage from './pages/MaterialsPage';
import HelpPage from './pages/HelpPage';

export default function App() {
  const { showTour, closeTour } = useTour();

  return (
    <BrowserRouter>
      {showTour && <Tour onClose={closeTour} />}
      <Layout demoMode={true}>
        <Routes>
          {/* Default route → classify */}
          <Route path="/" element={<Navigate to="/classify" replace />} />

          {/* Classify flow */}
          <Route path="/classify" element={<ClassifyPage />} />
          <Route path="/result/:eventId" element={<ResultPage />} />

          {/* Analytics */}
          <Route path="/analytics" element={<AnalyticsOverviewPage />} />
          <Route path="/analytics/ward/:wardId" element={<WardDetailPage />} />

          {/* Materials directory */}
          <Route path="/materials" element={<MaterialsPage />} />

          {/* Help */}
          <Route path="/help" element={<HelpPage />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/classify" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
