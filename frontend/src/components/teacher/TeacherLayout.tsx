import { useState } from 'react';
import type { ReactNode } from 'react';
import { TeacherSidebar } from './TeacherSidebar';
import { Breadcrumbs } from '@/components/Breadcrumbs';
import type { BreadcrumbItem } from '@/components/Breadcrumbs';

interface TeacherLayoutProps {
  children: ReactNode;
  breadcrumbs?: BreadcrumbItem[];
}

/**
 * Layout wrapper for all teacher pages
 * - Renders sidebar navigation (responsive)
 * - Renders breadcrumbs
 * - Handles mobile menu state
 */
export function TeacherLayout({ children, breadcrumbs = [] }: TeacherLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen((prev) => !prev);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <TeacherSidebar isOpen={isMobileMenuOpen} onClose={closeMobileMenu} />

      {/* Main Content Area */}
      <div className="md:pl-64">
        {/* Top bar with hamburger (mobile only) */}
        <div className="md:hidden sticky top-0 z-30 bg-white shadow-sm px-4 py-3 flex items-center">
          <button
            onClick={toggleMobileMenu}
            className="text-gray-700 hover:text-gray-900 transition-colors"
            aria-label="Open menu"
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
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          <h1 className="ml-3 text-lg font-semibold text-gray-900">
            Data Detective
          </h1>
        </div>

        {/* Content */}
        <main className="p-4 sm:p-6 lg:p-8">
          {/* Breadcrumbs */}
          {breadcrumbs && breadcrumbs.length > 0 && (
            <Breadcrumbs items={breadcrumbs} />
          )}

          {/* Page Content */}
          {children}
        </main>
      </div>
    </div>
  );
}

TeacherLayout.displayName = 'TeacherLayout';
