import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { DatabaseProvider } from '@/contexts/DatabaseContext';
import { ProtectedRoute } from '@/components/routing/ProtectedRoute';
import { RoleProtectedRoute } from '@/components/routing/RoleProtectedRoute';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ToastProvider } from '@/components/providers/ToastProvider';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ProfilePage } from '@/pages/ProfilePage';
import { PracticePage } from '@/pages/PracticePage';
import { ProgressPage } from '@/pages/ProgressPage';
import { LeaderboardPage } from '@/pages/LeaderboardPage';
import { DatasetsPage } from '@/pages/DatasetsPage';
import { DatasetUploadPage } from '@/pages/DatasetUploadPage';
import { DatasetDetailPage } from '@/pages/DatasetDetailPage';
import { ChallengeBuilderPage } from '@/pages/ChallengeBuilderPage';
import { ChallengeLibraryPage } from '@/pages/ChallengeLibraryPage';
import { StudentListPage } from '@/pages/teacher/StudentListPage';
import { StudentDetailPage } from '@/pages/teacher/StudentDetailPage';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastProvider>
          <DatabaseProvider>
            <AuthProvider>
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
                <Route path="/" element={<Navigate to="/practice" replace />} />
                <Route path="*" element={<Navigate to="/practice" replace />} />
              </Routes>
            </AuthProvider>
          </DatabaseProvider>
        </ToastProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
