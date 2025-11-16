import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

interface TeacherSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Navigation items for teacher sidebar
 */
const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/teacher/dashboard', icon: '🏠' },
  { label: 'Students', path: '/teacher/students', icon: '👥' },
  { label: 'Analytics', path: '/teacher/analytics', icon: '📊' },
  { label: 'Weekly Reports', path: '/teacher/reports/weekly', icon: '📝' },
  { label: 'Challenges', path: '/challenges/custom', icon: '🎯' },
  { label: 'Datasets', path: '/datasets', icon: '📁' },
  { label: 'Profile', path: '/profile', icon: '👤' },
];

/**
 * Teacher sidebar navigation component
 * - Fixed sidebar on desktop
 * - Overlay sidebar on mobile
 * - Active route highlighting
 * - User info and logout at bottom
 */
export function TeacherSidebar({ isOpen, onClose }: TeacherSidebarProps) {
  const { user, logout } = useAuth();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  return (
    <>
      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        aria-label="Teacher navigation sidebar"
        className={`
          fixed top-0 left-0 h-full w-64 bg-white shadow-lg z-50
          flex flex-col
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0
        `}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900 flex items-center">
                <span className="mr-2" aria-hidden="true">🔍</span>
                Data Detective
              </h1>
              <p className="text-xs text-gray-600 mt-1">Teacher Portal</p>
            </div>
            {/* Close button for mobile */}
            <button
              onClick={onClose}
              className="md:hidden text-gray-500 hover:text-gray-700 transition-colors"
              aria-label="Close menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 overflow-y-auto p-4" aria-label="Teacher menu">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;

              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={onClose} // Close mobile menu on navigation
                    aria-current={isActive ? 'page' : undefined}
                    className={`
                      flex items-center px-4 py-3 rounded-lg text-sm font-medium
                      transition-colors
                      ${
                        isActive
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 hover:bg-gray-100'
                      }
                    `}
                  >
                    <span className="mr-3 text-lg" aria-hidden="true">
                      {item.icon}
                    </span>
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer - User Info & Logout */}
        <div className="p-4 border-t border-gray-200">
          {user && (
            <div className="mb-3 px-2" role="region" aria-label="User information">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user.name}
              </p>
              <p className="text-xs text-gray-600 truncate">{user.email}</p>
              <p className="text-xs text-gray-500 capitalize mt-1">
                {user.role}
              </p>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            aria-label="Logout of your account"
          >
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}

TeacherSidebar.displayName = 'TeacherSidebar';
