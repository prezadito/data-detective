import { useState } from 'react';
import type { TableSchema } from '@/types';

export interface SchemaViewProps {
  /**
   * Optional: Filter to show only specific tables
   */
  tables?: string[];

  /**
   * Whether sections start expanded or collapsed
   * @default false (all collapsed)
   */
  defaultExpanded?: boolean;
}

/**
 * Hardcoded database schemas matching backend database.py
 * TODO: In future, fetch from backend endpoint or query sql.js database
 * Last updated: 2025-11-16
 */
const SCHEMAS: TableSchema[] = [
  {
    name: 'movies',
    columns: [
      { name: 'movie_id', type: 'INTEGER' },
      { name: 'title', type: 'TEXT' },
      { name: 'genre', type: 'TEXT' },
      { name: 'release_year', type: 'INTEGER' },
      { name: 'rating', type: 'REAL' },
      { name: 'length_min', type: 'INTEGER' },
    ],
    rowCount: 10,
  },
  {
    name: 'students',
    columns: [
      { name: 'student_id', type: 'INTEGER' },
      { name: 'name', type: 'TEXT' },
      { name: 'grade', type: 'TEXT' },
      { name: 'dietary_restrictions', type: 'TEXT' },
      { name: 'pizza_preference', type: 'TEXT' },
    ],
    rowCount: 10,
  },
  {
    name: 'video_games',
    columns: [
      { name: 'game_id', type: 'INTEGER' },
      { name: 'title', type: 'TEXT' },
      { name: 'platform', type: 'TEXT' },
      { name: 'genre', type: 'TEXT' },
      { name: 'year_released', type: 'INTEGER' },
      { name: 'units_sold', type: 'REAL' },
      { name: 'rating', type: 'REAL' },
    ],
    rowCount: 8,
  },
];

/**
 * Get badge color for column type
 */
function getTypeBadgeColor(type: 'INTEGER' | 'TEXT' | 'REAL'): string {
  switch (type) {
    case 'INTEGER':
      return 'bg-blue-100 text-blue-700';
    case 'TEXT':
      return 'bg-green-100 text-green-700';
    case 'REAL':
      return 'bg-purple-100 text-purple-700';
  }
}

/**
 * SchemaView component displays available database tables and columns
 * in an expandable/collapsible format
 */
export function SchemaView({ tables, defaultExpanded = false }: SchemaViewProps) {
  const [expandedTables, setExpandedTables] = useState<Set<string>>(
    () => (defaultExpanded ? new Set(SCHEMAS.map((s) => s.name)) : new Set())
  );

  // Filter schemas if specific tables requested
  const schemas = tables
    ? SCHEMAS.filter((schema) => tables.includes(schema.name))
    : SCHEMAS;

  /**
   * Toggle table expansion state
   */
  function toggleTable(tableName: string) {
    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (next.has(tableName)) {
        next.delete(tableName);
      } else {
        next.add(tableName);
      }
      return next;
    });
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-900 flex items-center">
          <span className="mr-2">📊</span>
          Available Tables
        </h3>
      </div>

      <div className="divide-y divide-gray-200">
        {schemas.map((schema) => {
          const isExpanded = expandedTables.has(schema.name);

          return (
            <div key={schema.name}>
              <button
                onClick={() => toggleTable(schema.name)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                aria-expanded={isExpanded}
                aria-controls={`schema-${schema.name}`}
              >
                <div className="flex items-center">
                  <span className="mr-2 text-gray-500">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                  <span className="font-medium text-gray-900">{schema.name}</span>
                  <span className="ml-2 text-sm text-gray-500">
                    ({schema.rowCount} rows)
                  </span>
                </div>
              </button>

              {isExpanded && (
                <div
                  id={`schema-${schema.name}`}
                  className="px-4 py-3 bg-gray-50"
                >
                  <ul className="space-y-2">
                    {schema.columns.map((column) => (
                      <li
                        key={column.name}
                        className="flex items-center justify-between"
                      >
                        <div className="flex items-center">
                          <span className="text-gray-400 mr-2">•</span>
                          <span className="text-sm font-mono text-gray-700">
                            {column.name}
                          </span>
                        </div>
                        <span
                          className={`px-2 py-0.5 text-xs font-medium rounded ${getTypeBadgeColor(
                            column.type
                          )}`}
                        >
                          {column.type}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

SchemaView.displayName = 'SchemaView';
