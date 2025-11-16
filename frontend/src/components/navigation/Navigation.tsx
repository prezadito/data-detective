import { useState } from 'react';
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
 * Includes mobile hamburger menu
 */
export function Navigation() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen((prev) => !prev);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  if (!user) {
    return null;
  }

  const navItems = getNavItems(user.role);

  return (
    <>
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            {/* Mobile Menu Button */}
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Toggle menu"
              aria-expanded={isMobileMenuOpen}
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {isMobileMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>

            {/* Logo / Brand */}
            <div className="flex items-center">
              <Link to="/practice" className="flex items-center">
                <h1 className="text-lg sm:text-xl font-bold text-gray-900">
                  Data Detective
                </h1>
              </Link>
            </div>

            {/* Desktop Navigation Links */}
            <div className="hidden md:flex items-center space-x-2 lg:space-x-4">
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

            {/* User Info & Logout (Desktop) */}
            <div className="hidden md:flex items-center gap-4">
              <div className="hidden lg:flex flex-col items-end">
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

            {/* Mobile Logout Button */}
            <div className="md:hidden">
              <Button onClick={handleLogout} variant="outline" size="sm">
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
            onClick={closeMobileMenu}
            aria-hidden="true"
          />

          {/* Mobile Menu Panel */}
          <div className="fixed top-16 left-0 right-0 bg-white shadow-lg z-50 md:hidden max-h-[calc(100vh-4rem)] overflow-y-auto">
            {/* User Info */}
            <div className="px-4 py-4 border-b border-gray-200 bg-gray-50">
              <p className="text-sm font-medium text-gray-900">{user.name}</p>
              <p className="text-xs text-gray-600">{user.email}</p>
              <p className="text-xs text-gray-500 capitalize mt-1">{user.role}</p>
            </div>

            {/* Navigation Links */}
            <nav className="py-2">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={closeMobileMenu}
                    className={`block px-4 py-3 text-base font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white border-l-4 border-blue-700'
                        : 'text-gray-700 hover:bg-gray-100 border-l-4 border-transparent'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </>
      )}
    </>
  );
}
