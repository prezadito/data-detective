import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryEditor } from '../QueryEditor';
import {
  createMockUseDatabase,
  createSuccessfulQueryResult,
  createQueryError,
} from '@/test/helpers/mockServices';
import { mockQueryResult, mockEmptyQueryResult, mockProgressResponse } from '@/test/helpers/mockData';
import { progressService } from '@/services/progressService';
import * as toastUtils from '@/utils/toast';

// Mock the useDatabase hook
const mockExecuteQuery = vi.fn();
const mockUseDatabase = createMockUseDatabase({
  executeQuery: mockExecuteQuery,
  isReady: true,
  queryHistory: [],
});

vi.mock('@/hooks/useDatabase', () => ({
  useDatabase: () => mockUseDatabase,
}));

// Mock progress service
vi.mock('@/services/progressService', () => ({
  progressService: {
    submitChallenge: vi.fn(),
  },
}));

// Mock toast utilities
vi.mock('@/utils/toast', () => ({
  showSuccessToast: vi.fn(),
  showErrorToast: vi.fn(),
  showApiErrorToast: vi.fn(),
}));

// Mock validateQueryResults
vi.mock('@/utils/validateQuery', () => ({
  validateQueryResults: vi.fn((studentResult, expectedResult) => ({
    isValid: JSON.stringify(studentResult) === JSON.stringify(expectedResult),
    message: JSON.stringify(studentResult) === JSON.stringify(expectedResult)
      ? 'Query is correct!'
      : 'Query results do not match expected output',
  })),
}));

describe('QueryEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockExecuteQuery.mockReturnValue(mockQueryResult);
    vi.mocked(progressService.submitChallenge).mockResolvedValue(mockProgressResponse);
  });

  describe('Rendering', () => {
    it('renders textarea with placeholder', () => {
      render(<QueryEditor />);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i });
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveAttribute('placeholder', expect.stringContaining('Enter your SQL query'));
    });

    it('renders Run Query and Clear buttons', () => {
      render(<QueryEditor />);

      expect(screen.getByRole('button', { name: /run query/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
    });

    it('shows Check Answer and Submit buttons when expectedQuery provided', () => {
      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
        />
      );

      expect(screen.getByRole('button', { name: /check answer/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^submit$/i })).toBeInTheDocument();
    });

    it('does not show Check Answer and Submit without expectedQuery', () => {
      render(<QueryEditor />);

      expect(screen.queryByRole('button', { name: /check answer/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /^submit$/i })).not.toBeInTheDocument();
    });

    it('shows query history when showHistory is true', () => {
      const historyEntry = {
        id: '1',
        query: 'SELECT * FROM users',
        timestamp: new Date(),
        success: true,
        rowCount: 5,
        executionTime: 12.5,
      };

      mockUseDatabase.queryHistory = [historyEntry];

      render(<QueryEditor showHistory={true} />);

      expect(screen.getByText(/recent queries/i)).toBeInTheDocument();
      expect(screen.getByText('SELECT * FROM users')).toBeInTheDocument();
    });

    it('does not show history when showHistory is false', () => {
      const historyEntry = {
        id: '1',
        query: 'SELECT * FROM users',
        timestamp: new Date(),
        success: true,
      };

      mockUseDatabase.queryHistory = [historyEntry];

      render(<QueryEditor showHistory={false} />);

      expect(screen.queryByText(/recent queries/i)).not.toBeInTheDocument();
    });
  });

  describe('Initial State', () => {
    it('loads with initialQuery prop', () => {
      render(<QueryEditor initialQuery="SELECT * FROM users" />);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i }) as HTMLTextAreaElement;
      expect(textarea.value).toBe('SELECT * FROM users');
    });

    it('auto-focuses textarea on mount', () => {
      render(<QueryEditor />);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i });
      expect(textarea).toHaveFocus();
    });

    it('disables all buttons when database not ready', () => {
      mockUseDatabase.isReady = false;

      render(<QueryEditor />);

      expect(screen.getByRole('button', { name: /run query/i })).toBeDisabled();
      expect(screen.getByRole('textbox', { name: /sql query input/i })).toBeDisabled();
      expect(screen.getByText(/database is loading/i)).toBeInTheDocument();

      // Reset for other tests
      mockUseDatabase.isReady = true;
    });
  });

  describe('Query Execution', () => {
    it('executes query when Run Query clicked', async () => {
      const user = userEvent.setup();
      render(<QueryEditor />);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i });
      await user.type(textarea, 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /run query/i }));

      expect(mockExecuteQuery).toHaveBeenCalledWith('SELECT * FROM users');
    });

    it('displays results table with correct data', async () => {
      const user = userEvent.setup();
      render(<QueryEditor />);

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /run query/i }));

      await waitFor(() => {
        expect(screen.getByText('Results')).toBeInTheDocument();
        expect(screen.getByText('3 rows')).toBeInTheDocument();
        expect(screen.getByText('Alice')).toBeInTheDocument();
        expect(screen.getByText('Bob')).toBeInTheDocument();
        expect(screen.getByText('Charlie')).toBeInTheDocument();
      });
    });

    it('shows execution time', async () => {
      const user = userEvent.setup();
      render(<QueryEditor />);

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /run query/i }));

      await waitFor(() => {
        expect(screen.getByText(/query executed successfully in \d+\.\d+ms/i)).toBeInTheDocument();
      });
    });

    it('shows error message on SQL syntax error', async () => {
      const user = userEvent.setup();
      mockExecuteQuery.mockImplementation(() => {
        throw createQueryError('Syntax error near SELECT');
      });

      render(<QueryEditor />);

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELCT * FROM users');
      await user.click(screen.getByRole('button', { name: /run query/i }));

      await waitFor(() => {
        expect(screen.getByText(/query error/i)).toBeInTheDocument();
        expect(screen.getByText(/syntax error near select/i)).toBeInTheDocument();
      });
    });

    it('shows "no rows" message when query returns empty result', async () => {
      const user = userEvent.setup();
      mockExecuteQuery.mockReturnValue(mockEmptyQueryResult);

      render(<QueryEditor />);

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users WHERE id = 999');
      await user.click(screen.getByRole('button', { name: /run query/i }));

      await waitFor(() => {
        expect(screen.getByText(/query executed successfully but returned no rows/i)).toBeInTheDocument();
      });
    });

    it('disables run button when query is empty', () => {
      render(<QueryEditor />);

      const runButton = screen.getByRole('button', { name: /run query/i });
      expect(runButton).toBeDisabled();
    });

    it('calls onQueryExecute callback when query succeeds', async () => {
      const user = userEvent.setup();
      const onQueryExecute = vi.fn();

      render(<QueryEditor onQueryExecute={onQueryExecute} />);

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /run query/i }));

      await waitFor(() => {
        expect(onQueryExecute).toHaveBeenCalledWith(mockQueryResult);
      });
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('Ctrl+Enter executes query', async () => {
      const user = userEvent.setup();
      render(<QueryEditor />);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i });
      await user.type(textarea, 'SELECT * FROM users');
      await user.keyboard('{Control>}{Enter}{/Control}');

      expect(mockExecuteQuery).toHaveBeenCalledWith('SELECT * FROM users');
    });

    it('Cmd+Enter executes query on Mac', async () => {
      const user = userEvent.setup();
      render(<QueryEditor />);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i });
      await user.type(textarea, 'SELECT * FROM users');
      await user.keyboard('{Meta>}{Enter}{/Meta}');

      expect(mockExecuteQuery).toHaveBeenCalledWith('SELECT * FROM users');
    });

    it('Ctrl+K clears editor', async () => {
      const user = userEvent.setup();
      render(<QueryEditor initialQuery="SELECT * FROM users" />);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i }) as HTMLTextAreaElement;
      expect(textarea.value).toBe('SELECT * FROM users');

      await user.click(textarea);
      await user.keyboard('{Control>}k{/Control}');

      expect(textarea.value).toBe('');
    });

    it('Escape dismisses error message', async () => {
      const user = userEvent.setup();
      mockExecuteQuery.mockImplementation(() => {
        throw createQueryError('Syntax error');
      });

      render(<QueryEditor />);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i });
      await user.type(textarea, 'BAD SQL');
      await user.click(screen.getByRole('button', { name: /run query/i }));

      await waitFor(() => {
        expect(screen.getByText(/syntax error/i)).toBeInTheDocument();
      });

      await user.click(textarea);
      await user.keyboard('{Escape}');

      expect(screen.queryByText(/syntax error/i)).not.toBeInTheDocument();
    });
  });

  describe('Query Validation', () => {
    it('validates query against expected output', async () => {
      const user = userEvent.setup();
      const expectedResult = createSuccessfulQueryResult();
      mockExecuteQuery.mockReturnValue(expectedResult);

      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
        />
      );

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /check answer/i }));

      await waitFor(() => {
        expect(toastUtils.showSuccessToast).toHaveBeenCalledWith('Query is correct! You can now submit.');
      });
    });

    it('shows success message when query is correct', async () => {
      const user = userEvent.setup();
      const expectedResult = createSuccessfulQueryResult();
      mockExecuteQuery.mockReturnValue(expectedResult);

      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
        />
      );

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /check answer/i }));

      await waitFor(() => {
        expect(screen.getByText('Query is correct!')).toBeInTheDocument();
      });
    });

    it('shows error message when query results do not match', async () => {
      const user = userEvent.setup();
      const wrongResult = createSuccessfulQueryResult({ values: [[999, 'Wrong']] });
      mockExecuteQuery
        .mockReturnValueOnce(wrongResult) // Student's query
        .mockReturnValueOnce(mockQueryResult); // Expected query

      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
        />
      );

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM products');
      await user.click(screen.getByRole('button', { name: /check answer/i }));

      await waitFor(() => {
        expect(toastUtils.showErrorToast).toHaveBeenCalledWith('Query results do not match expected output');
      });
    });
  });

  describe('Challenge Submission', () => {
    it('submit button is disabled until query is validated', () => {
      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
        />
      );

      expect(screen.getByRole('button', { name: /^submit$/i })).toBeDisabled();
    });

    it('calls progressService.submitChallenge with correct data', async () => {
      const user = userEvent.setup();
      const expectedResult = createSuccessfulQueryResult();
      mockExecuteQuery.mockReturnValue(expectedResult);
      vi.mocked(progressService.submitChallenge).mockResolvedValue(mockProgressResponse);

      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={2}
          hintsUsed={1}
        />
      );

      // First validate
      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /check answer/i }));

      await waitFor(() => {
        expect(screen.getByText('Query is correct!')).toBeInTheDocument();
      });

      // Then submit
      await user.click(screen.getByRole('button', { name: /^submit$/i }));

      await waitFor(() => {
        expect(progressService.submitChallenge).toHaveBeenCalledWith({
          unit_id: 1,
          challenge_id: 2,
          query: 'SELECT * FROM users',
          hints_used: 1,
        });
      });
    });

    it('calls onSubmitSuccess callback with response', async () => {
      const user = userEvent.setup();
      const onSubmitSuccess = vi.fn();
      const expectedResult = createSuccessfulQueryResult();
      mockExecuteQuery.mockReturnValue(expectedResult);
      vi.mocked(progressService.submitChallenge).mockResolvedValue(mockProgressResponse);

      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
          onSubmitSuccess={onSubmitSuccess}
        />
      );

      // Validate then submit
      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /check answer/i }));

      await waitFor(() => {
        expect(screen.getByText('Query is correct!')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /^submit$/i }));

      await waitFor(() => {
        expect(onSubmitSuccess).toHaveBeenCalledWith(mockProgressResponse);
      });
    });

    it('shows error if submitting without validation', async () => {
      const user = userEvent.setup();
      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
        />
      );

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');

      // Try to submit without validating
      // Submit button should be disabled, so this shouldn't be possible
      expect(screen.getByRole('button', { name: /^submit$/i })).toBeDisabled();
    });

    it('shows success toast on successful submission', async () => {
      const user = userEvent.setup();
      const expectedResult = createSuccessfulQueryResult();
      mockExecuteQuery.mockReturnValue(expectedResult);
      vi.mocked(progressService.submitChallenge).mockResolvedValue(mockProgressResponse);

      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
        />
      );

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /check answer/i }));

      await waitFor(() => {
        expect(screen.getByText('Query is correct!')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /^submit$/i }));

      await waitFor(() => {
        expect(toastUtils.showSuccessToast).toHaveBeenCalledWith(
          expect.stringContaining('Challenge completed!')
        );
      });
    });
  });

  describe('Loading States', () => {
    it('enables run button when query is entered', async () => {
      const user = userEvent.setup();
      render(<QueryEditor />);

      const runButton = screen.getByRole('button', { name: /run query/i });
      expect(runButton).toBeDisabled();

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');

      // Button should be enabled after typing
      expect(runButton).not.toBeDisabled();
    });

    it('shows loading state during submission', async () => {
      const user = userEvent.setup();
      const expectedResult = createSuccessfulQueryResult();
      mockExecuteQuery.mockReturnValue(expectedResult);
      vi.mocked(progressService.submitChallenge).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockProgressResponse), 100))
      );

      render(
        <QueryEditor
          expectedQuery="SELECT * FROM users"
          unitId={1}
          challengeId={1}
        />
      );

      await user.type(screen.getByRole('textbox', { name: /sql query input/i }), 'SELECT * FROM users');
      await user.click(screen.getByRole('button', { name: /check answer/i }));

      await waitFor(() => {
        expect(screen.getByText('Query is correct!')).toBeInTheDocument();
      });

      const submitButton = screen.getByRole('button', { name: /^submit$/i });
      await user.click(submitButton);

      // Button should be disabled during submission
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Clear Functionality', () => {
    it('clears query, results, and errors when Clear clicked', async () => {
      const user = userEvent.setup();
      render(<QueryEditor initialQuery="SELECT * FROM users" />);

      // Execute query to get results
      await user.click(screen.getByRole('button', { name: /run query/i }));

      await waitFor(() => {
        expect(screen.getByText('Results')).toBeInTheDocument();
      });

      // Clear everything
      await user.click(screen.getByRole('button', { name: /clear/i }));

      const textarea = screen.getByRole('textbox', { name: /sql query input/i }) as HTMLTextAreaElement;
      expect(textarea.value).toBe('');
      expect(screen.queryByText('Results')).not.toBeInTheDocument();
    });

    it('refocuses textarea after clearing', async () => {
      const user = userEvent.setup();
      render(<QueryEditor initialQuery="SELECT * FROM users" />);

      await user.click(screen.getByRole('button', { name: /clear/i }));

      const textarea = screen.getByRole('textbox', { name: /sql query input/i });
      expect(textarea).toHaveFocus();
    });
  });

  describe('Query History', () => {
    it('displays recent queries in history', () => {
      const historyEntries = [
        {
          id: '1',
          query: 'SELECT * FROM users',
          timestamp: new Date(Date.now() - 60000), // 1 min ago
          success: true,
          rowCount: 5,
          executionTime: 12.5,
        },
        {
          id: '2',
          query: 'SELECT COUNT(*) FROM products',
          timestamp: new Date(Date.now() - 120000), // 2 min ago
          success: true,
          rowCount: 1,
          executionTime: 8.2,
        },
      ];

      mockUseDatabase.queryHistory = historyEntries;

      render(<QueryEditor />);

      expect(screen.getByText('SELECT * FROM users')).toBeInTheDocument();
      expect(screen.getByText('SELECT COUNT(*) FROM products')).toBeInTheDocument();
    });

    it('loads query from history when clicked', async () => {
      const user = userEvent.setup();
      const historyEntry = {
        id: '1',
        query: 'SELECT * FROM users',
        timestamp: new Date(),
        success: true,
      };

      mockUseDatabase.queryHistory = [historyEntry];

      render(<QueryEditor />);

      const historyItem = screen.getByText('SELECT * FROM users');
      await user.click(historyItem.closest('div')!);

      const textarea = screen.getByRole('textbox', { name: /sql query input/i }) as HTMLTextAreaElement;
      expect(textarea.value).toBe('SELECT * FROM users');
    });

    it('limits history to maxHistoryEntries', () => {
      const historyEntries = Array.from({ length: 10 }, (_, i) => ({
        id: String(i),
        query: `SELECT ${i} FROM users`,
        timestamp: new Date(),
        success: true,
      }));

      mockUseDatabase.queryHistory = historyEntries;

      render(<QueryEditor maxHistoryEntries={3} />);

      // Should only show 3 entries
      expect(screen.getByText('SELECT 0 FROM users')).toBeInTheDocument();
      expect(screen.getByText('SELECT 1 FROM users')).toBeInTheDocument();
      expect(screen.getByText('SELECT 2 FROM users')).toBeInTheDocument();
      expect(screen.queryByText('SELECT 3 FROM users')).not.toBeInTheDocument();
    });
  });
});
