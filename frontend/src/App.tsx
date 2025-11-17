import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { DatabaseProvider } from '@/contexts/DatabaseContext';
import { ProtectedRoute } from '@/components/routing/ProtectedRoute';
import { RoleProtectedRoute } from '@/components/routing/RoleProtectedRoute';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ToastProvider } from '@/components/providers/ToastProvider';
import { Navigation } from '@/components/navigation/Navigation';
import { SkipLink } from '@/components/ui/SkipLink';
import { OfflineNotice } from '@/components/OfflineNotice';

// Lazy load all route components for code splitting
// Note: Pages use named exports, so we use .then() to map to default export
const LoginPage = lazy(() => import('@/pages/LoginPage').then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('@/pages/RegisterPage').then(m => ({ default: m.RegisterPage })));
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const ProfilePage = lazy(() => import('@/pages/ProfilePage').then(m => ({ default: m.ProfilePage })));
const PracticePage = lazy(() => import('@/pages/PracticePage').then(m => ({ default: m.PracticePage })));
const ProgressPage = lazy(() => import('@/pages/ProgressPage').then(m => ({ default: m.ProgressPage })));
const LeaderboardPage = lazy(() => import('@/pages/LeaderboardPage').then(m => ({ default: m.LeaderboardPage })));
const DatasetsPage = lazy(() => import('@/pages/DatasetsPage').then(m => ({ default: m.DatasetsPage })));
const DatasetUploadPage = lazy(() => import('@/pages/DatasetUploadPage').then(m => ({ default: m.DatasetUploadPage })));
const DatasetDetailPage = lazy(() => import('@/pages/DatasetDetailPage').then(m => ({ default: m.DatasetDetailPage })));
const ChallengeBuilderPage = lazy(() => import('@/pages/ChallengeBuilderPage').then(m => ({ default: m.ChallengeBuilderPage })));
const ChallengeLibraryPage = lazy(() => import('@/pages/ChallengeLibraryPage').then(m => ({ default: m.ChallengeLibraryPage })));
const StudentListPage = lazy(() => import('@/pages/teacher/StudentListPage').then(m => ({ default: m.StudentListPage })));
const StudentDetailPage = lazy(() => import('@/pages/teacher/StudentDetailPage').then(m => ({ default: m.StudentDetailPage })));
const AnalyticsPage = lazy(() => import('@/pages/teacher/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const WeeklyReportPage = lazy(() => import('@/pages/teacher/WeeklyReportPage').then(m => ({ default: m.WeeklyReportPage })));
const TeacherDashboard = lazy(() => import('@/pages/teacher/Dashboard').then(m => ({ default: m.Dashboard })));

/**
 * Loading fallback component displayed while lazy-loaded routes are loading
 */
function RouteLoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600">Loading...</p>
      </div>
    </div>
  );
}

/**
 * Layout wrapper that conditionally renders Navigation
 * Only shows navigation on authenticated pages (not login/register)
 * Teacher routes use TeacherLayout with sidebar instead
 */
function AppLayout() {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  const isTeacherRoute = location.pathname.startsWith('/teacher');

  return (
    <>
      <OfflineNotice />
      <SkipLink />
      {!isAuthPage && !isTeacherRoute && <Navigation />}
      <Suspense fallback={<RouteLoadingFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/practice"
          element={
            <ProtectedRoute>
              <PracticePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/progress"
          element={
            <ProtectedRoute>
              <ProgressPage />
            </ProtectedRoute>
          }
        />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/datasets"
          element={
            <ProtectedRoute>
              <DatasetsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/datasets/upload"
          element={
            <ProtectedRoute>
              <DatasetUploadPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/datasets/:id"
          element={
            <ProtectedRoute>
              <DatasetDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/challenges/custom/new"
          element={
            <ProtectedRoute>
              <ChallengeBuilderPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/challenges/custom"
          element={
            <ProtectedRoute>
              <ChallengeLibraryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/dashboard"
          element={
            <RoleProtectedRoute requiredRole="teacher">
              <TeacherDashboard />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="/teacher/students"
          element={
            <RoleProtectedRoute requiredRole="teacher">
              <StudentListPage />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="/teacher/students/:id"
          element={
            <RoleProtectedRoute requiredRole="teacher">
              <StudentDetailPage />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="/teacher/analytics"
          element={
            <RoleProtectedRoute requiredRole="teacher">
              <AnalyticsPage />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="/teacher/reports/weekly"
          element={
            <RoleProtectedRoute requiredRole="teacher">
              <WeeklyReportPage />
            </RoleProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/practice" replace />} />
        <Route path="*" element={<Navigate to="/practice" replace />} />
        </Routes>
      </Suspense>
    </>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastProvider>
          <DatabaseProvider>
            <AuthProvider>
              <AppLayout />
            </AuthProvider>
          </DatabaseProvider>
        </ToastProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
