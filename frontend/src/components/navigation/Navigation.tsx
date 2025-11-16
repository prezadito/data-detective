import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import type { UserRole } from '@/types';

interface NavItem {
  label: string;
  path: string;
}

/**
 * Navigation items for students
 */
const studentNavItems: NavItem[] = [
  { label: 'Practice', path: '/practice' },
  { label: 'Progress', path: '/progress' },
  { label: 'Leaderboard', path: '/leaderboard' },
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Profile', path: '/profile' },
];

/**
 * Navigation items for teachers
 */
const teacherNavItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Datasets', path: '/datasets' },
  { label: 'Challenges', path: '/challenges/custom' },
  { label: 'Students', path: '/teacher/students' },
  { label: 'Analytics', path: '/teacher/analytics' },
  { label: 'Weekly Reports', path: '/teacher/reports/weekly' },
  { label: 'Profile', path: '/profile' },
];

/**
 * Get navigation items based on user role
 */
function getNavItems(role: UserRole): NavItem[] {
  return role === 'teacher' ? teacherNavItems : studentNavItems;
}

/**
 * Main navigation bar for authenticated users
 * Shows role-based navigation links and logout button
 */
export function Navigation() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  if (!user) {
    return null;
  }

  const navItems = getNavItems(user.role);

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo / Brand */}
          <div className="flex items-center">
            <Link to="/practice" className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                Data Detective
              </h1>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-4">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* User Info & Logout */}
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-sm text-gray-700 font-medium">
                {user.name}
              </span>
              <span className="text-xs text-gray-500 capitalize">
                {user.role}
              </span>
            </div>
            <Button onClick={handleLogout} variant="outline" size="sm">
              Logout
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
