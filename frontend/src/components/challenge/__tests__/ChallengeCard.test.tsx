import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChallengeCard } from '../ChallengeCard';
import { mockChallengeDetail } from '@/test/helpers/mockData';
import type { ChallengeDetail } from '@/types';

// Mock child components to test ChallengeCard in isolation
vi.mock('../SchemaView', () => ({
  SchemaView: ({ defaultExpanded }: { defaultExpanded?: boolean }) => (
    <div data-testid="schema-view">SchemaView (expanded: {String(defaultExpanded)})</div>
  ),
}));

vi.mock('../ExpectedOutput', () => ({
  ExpectedOutput: ({
    query,
    showQuery,
    maxRows,
  }: {
    query: string;
    showQuery?: boolean;
    maxRows?: number;
  }) => (
    <div data-testid="expected-output">
      ExpectedOutput (query: {query}, showQuery: {String(showQuery)}, maxRows: {maxRows})
    </div>
  ),
}));

vi.mock('../HintSystem', () => ({
  HintSystem: ({
    unitId,
    challengeId,
    onHintsUsedChange,
    initialHintsUsed,
  }: {
    unitId: number;
    challengeId: number;
    hints: string[];
    onHintsUsedChange?: (count: number) => void;
    initialHintsUsed?: number;
  }) => (
    <div data-testid="hint-system">
      HintSystem (unit: {unitId}, challenge: {challengeId}, initial: {initialHintsUsed})
      <button onClick={() => onHintsUsedChange?.(1)}>Use Hint</button>
    </div>
  ),
}));

vi.mock('@/data/challengeHints', () => ({
  getChallengeHints: () => ['Hint 1', 'Hint 2', 'Hint 3'],
}));

describe('ChallengeCard', () => {
  let challenge: ChallengeDetail;

  beforeEach(() => {
    vi.clearAllMocks();
    challenge = { ...mockChallengeDetail };
  });

  describe('Rendering', () => {
    it('renders challenge title and unit/challenge IDs', () => {
      render(<ChallengeCard challenge={challenge} />);

      expect(screen.getByText('SELECT All Columns')).toBeInTheDocument();
      expect(screen.getByText(/Unit 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Challenge 1/i)).toBeInTheDocument();
    });

    it('renders points badge', () => {
      render(<ChallengeCard challenge={challenge} />);

      expect(screen.getByText(/100 pts/i)).toBeInTheDocument();
    });

    it('renders description', () => {
      render(<ChallengeCard challenge={challenge} />);

      expect(
        screen.getByText('Write a query to select all columns from the users table.')
      ).toBeInTheDocument();
    });

    it('renders completion statistics', () => {
      render(<ChallengeCard challenge={challenge} />);

      // Completion rate
      expect(screen.getByText(/75\.5%/i)).toBeInTheDocument();
      expect(screen.getByText(/completion/i)).toBeInTheDocument();

      // Average attempts
      expect(screen.getByText(/2\.3/i)).toBeInTheDocument();
      expect(screen.getByText(/attempts/i)).toBeInTheDocument();

      // Success count
      expect(screen.getByText('75')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText(/successful/i)).toBeInTheDocument();
    });

    it('renders sample query when showSampleQuery is true', () => {
      render(<ChallengeCard challenge={challenge} showSampleQuery={true} />);

      // ExpectedOutput component should receive showQuery=true
      expect(screen.getByTestId('expected-output')).toHaveTextContent('showQuery: true');
    });

    it('does not show sample query by default', () => {
      render(<ChallengeCard challenge={challenge} />);

      // ExpectedOutput should receive showQuery=false by default
      expect(screen.getByTestId('expected-output')).toHaveTextContent('showQuery: false');
    });
  });

  describe('Conditional Rendering', () => {
    it('shows SchemaView when showSchema is true', () => {
      render(<ChallengeCard challenge={challenge} showSchema={true} />);

      expect(screen.getByTestId('schema-view')).toBeInTheDocument();
    });

    it('hides SchemaView when showSchema is false', () => {
      render(<ChallengeCard challenge={challenge} showSchema={false} />);

      expect(screen.queryByTestId('schema-view')).not.toBeInTheDocument();
    });

    it('shows ExpectedOutput when showExpectedOutput is true', () => {
      render(<ChallengeCard challenge={challenge} showExpectedOutput={true} />);

      expect(screen.getByTestId('expected-output')).toBeInTheDocument();
    });

    it('hides ExpectedOutput when showExpectedOutput is false', () => {
      render(<ChallengeCard challenge={challenge} showExpectedOutput={false} />);

      expect(screen.queryByTestId('expected-output')).not.toBeInTheDocument();
    });

    it('shows HintSystem when showHints is true', () => {
      render(<ChallengeCard challenge={challenge} showHints={true} />);

      expect(screen.getByTestId('hint-system')).toBeInTheDocument();
    });

    it('hides HintSystem when showHints is false', () => {
      render(<ChallengeCard challenge={challenge} showHints={false} />);

      expect(screen.queryByTestId('hint-system')).not.toBeInTheDocument();
    });

    it('shows all components by default', () => {
      render(<ChallengeCard challenge={challenge} />);

      expect(screen.getByTestId('schema-view')).toBeInTheDocument();
      expect(screen.getByTestId('expected-output')).toBeInTheDocument();
      expect(screen.getByTestId('hint-system')).toBeInTheDocument();
    });
  });

  describe('State Management', () => {
    it('initializes with initialHintsUsed', () => {
      render(<ChallengeCard challenge={challenge} initialHintsUsed={2} />);

      expect(screen.getByTestId('hint-system')).toHaveTextContent('initial: 2');
    });

    it('calls onHintsUsedChange when hints are accessed', async () => {
      const user = userEvent.setup();
      const onHintsUsedChange = vi.fn();

      render(
        <ChallengeCard
          challenge={challenge}
          onHintsUsedChange={onHintsUsedChange}
        />
      );

      // Simulate using a hint (mocked HintSystem button)
      const useHintButton = screen.getByText('Use Hint');
      await user.click(useHintButton);

      expect(onHintsUsedChange).toHaveBeenCalledWith(1);
    });

    it('defaults to 0 hints used when initialHintsUsed not provided', () => {
      render(<ChallengeCard challenge={challenge} />);

      expect(screen.getByTestId('hint-system')).toHaveTextContent('initial: 0');
    });
  });

  describe('Variant Support', () => {
    it('renders full variant correctly', () => {
      render(<ChallengeCard challenge={challenge} variant="full" />);

      expect(screen.getByText('SELECT All Columns')).toBeInTheDocument();
      expect(screen.getByTestId('schema-view')).toBeInTheDocument();
    });

    it('logs warning for unimplemented variants', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      render(<ChallengeCard challenge={challenge} variant="preview" />);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining("Variant 'preview' not yet implemented")
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('Props Integration', () => {
    it('passes correct props to SchemaView', () => {
      render(<ChallengeCard challenge={challenge} />);

      const schemaView = screen.getByTestId('schema-view');
      expect(schemaView).toHaveTextContent('expanded: false');
    });

    it('passes correct props to ExpectedOutput', () => {
      render(<ChallengeCard challenge={challenge} showSampleQuery={true} />);

      const expectedOutput = screen.getByTestId('expected-output');
      expect(expectedOutput).toHaveTextContent('query: SELECT * FROM users');
      expect(expectedOutput).toHaveTextContent('showQuery: true');
      expect(expectedOutput).toHaveTextContent('maxRows: 5');
    });

    it('passes correct props to HintSystem', () => {
      render(<ChallengeCard challenge={challenge} initialHintsUsed={3} />);

      const hintSystem = screen.getByTestId('hint-system');
      expect(hintSystem).toHaveTextContent('unit: 1');
      expect(hintSystem).toHaveTextContent('challenge: 1');
      expect(hintSystem).toHaveTextContent('initial: 3');
    });
  });
});
