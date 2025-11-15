import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';

export function DashboardPage() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-bold text-gray-900">Data Detective</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-700">
                Welcome, <span className="font-medium">{user?.email}</span>
              </span>
              <Button onClick={handleLogout} variant="outline" size="sm">
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h2>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
              <p className="text-sm text-blue-700">
                <strong>User ID:</strong> {user?.id}
              </p>
              <p className="text-sm text-blue-700">
                <strong>Email:</strong> {user?.email}
              </p>
              <p className="text-sm text-blue-700">
                <strong>Role:</strong> {user?.role}
              </p>
            </div>
            <p className="text-gray-600">
              This is a placeholder dashboard. You can now build out the challenge
              functionality!
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
