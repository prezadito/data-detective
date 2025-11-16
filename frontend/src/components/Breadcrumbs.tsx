import { Link } from 'react-router-dom';

export interface BreadcrumbItem {
  label: string;
  path?: string; // undefined for current page
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

/**
 * Breadcrumbs navigation component
 * Shows navigation hierarchy with clickable links
 */
export function Breadcrumbs({ items }: BreadcrumbsProps) {
  // Don't render if no items or only one item
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="mb-6">
      <ol className="flex items-center space-x-2 text-sm">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          const isFirst = index === 0;

          return (
            <li key={index} className="flex items-center">
              {/* Separator (except for first item) */}
              {!isFirst && (
                <span className="mx-2 text-gray-400" aria-hidden="true">
                  /
                </span>
              )}

              {/* Current page (last item, no link) */}
              {isLast ? (
                <span className="font-medium text-gray-900">
                  {isFirst && <span className="mr-1.5">🏠</span>}
                  {item.label}
                </span>
              ) : (
                /* Breadcrumb link */
                <Link
                  to={item.path || '#'}
                  className="text-gray-600 hover:text-gray-900 transition-colors"
                >
                  {isFirst && <span className="mr-1.5">🏠</span>}
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

Breadcrumbs.displayName = 'Breadcrumbs';
