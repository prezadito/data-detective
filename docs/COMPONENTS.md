# Component Library

Complete reference for all React components in the Data Detective Academy frontend.

## Table of Contents

- [Component Organization](#component-organization)
- [UI Components](#ui-components)
- [Authentication Components](#authentication-components)
- [Challenge Components](#challenge-components)
- [Query Components](#query-components)
- [Progress Components](#progress-components)
- [Leaderboard Components](#leaderboard-components)
- [Teacher Components](#teacher-components)
- [Navigation Components](#navigation-components)
- [Routing Components](#routing-components)
- [Provider Components](#provider-components)
- [Component Best Practices](#component-best-practices)

---

## Component Organization

Components are organized by feature domain:

```
src/components/
├── auth/              # Authentication forms
├── challenge/         # Challenge-related UI
├── leaderboard/       # Leaderboard displays
├── navigation/        # Navigation bar
├── progress/          # Progress tracking
├── query/             # SQL query editor
├── routing/           # Route protection
├── teacher/           # Teacher dashboard
├── ui/                # Reusable UI primitives
└── providers/         # Context providers
```

---

## UI Components

### Button

Generic reusable button component.

**Location:** `src/components/ui/Button.tsx`

**Props:**
```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}
```

**Usage:**
```tsx
import { Button } from '@/components/ui/Button';

<Button variant="primary" size="md" onClick={handleClick}>
  Submit
</Button>

<Button variant="danger" loading={isLoading}>
  Delete
</Button>
```

**Variants:**
- `primary`: Blue background, white text (default)
- `secondary`: Gray background, dark text
- `danger`: Red background, white text
- `ghost`: Transparent background, colored text

---

### Input

Form input component with validation support.

**Location:** `src/components/ui/Input.tsx`

**Props:**
```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}
```

**Usage:**
```tsx
import { Input } from '@/components/ui/Input';

<Input
  label="Email"
  type="email"
  placeholder="student@example.com"
  error={errors.email?.message}
  {...register('email')}
/>
```

**Features:**
- Automatic error styling
- Label support
- Helper text
- Accessible (aria-labels)

---

### Modal

Modal/dialog component.

**Location:** `src/components/ui/Modal.tsx`

**Props:**
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}
```

**Usage:**
```tsx
import { Modal } from '@/components/ui/Modal';
import { useState } from 'react';

function Example() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Open Modal</Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Challenge Hint"
        size="md"
      >
        <p>Here's your hint...</p>
      </Modal>
    </>
  );
}
```

**Features:**
- Backdrop click to close
- ESC key to close
- Focus trap
- Portal rendering
- Accessible (ARIA)

---

### LoadingSpinner

Loading indicator component.

**Location:** `src/components/ui/LoadingSpinner.tsx`

**Props:**
```typescript
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}
```

**Usage:**
```tsx
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

<LoadingSpinner size="md" label="Loading challenges..." />
```

---

### ErrorMessage

Error message display component.

**Location:** `src/components/ui/ErrorMessage.tsx`

**Props:**
```typescript
interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}
```

**Usage:**
```tsx
import { ErrorMessage } from '@/components/ui/ErrorMessage';

<ErrorMessage
  message="Failed to load challenges"
  onRetry={refetchChallenges}
/>
```

---

### ErrorBoundary

React error boundary for graceful error handling.

**Location:** `src/components/ui/ErrorBoundary.tsx`

**Props:**
```typescript
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}
```

**Usage:**
```tsx
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

<ErrorBoundary>
  <App />
</ErrorBoundary>
```

**Features:**
- Catches React component errors
- Displays user-friendly error message
- Logs errors to console
- Optional custom fallback UI

---

### SkipLink

Accessibility skip-to-content link.

**Location:** `src/components/ui/SkipLink.tsx`

**Usage:**
```tsx
import { SkipLink } from '@/components/ui/SkipLink';

// In App.tsx
<SkipLink href="#main-content">Skip to main content</SkipLink>
```

**Accessibility:**
- Hidden by default
- Visible on focus
- Keyboard accessible
- WCAG 2.1 AA compliant

---

## Authentication Components

### LoginForm

User login form with validation.

**Location:** `src/components/auth/LoginForm.tsx`

**Props:**
```typescript
interface LoginFormProps {
  onSuccess?: () => void;
}
```

**Usage:**
```tsx
import { LoginForm } from '@/components/auth/LoginForm';

<LoginForm onSuccess={() => navigate('/dashboard')} />
```

**Features:**
- Email and password validation
- Form validation with Zod
- React Hook Form integration
- Error handling
- Loading states
- "Remember me" checkbox
- "Forgot password" link

**Form Fields:**
- Email (required, valid email)
- Password (required, min 8 chars)

---

### RegisterForm

User registration form.

**Location:** `src/components/auth/RegisterForm.tsx`

**Props:**
```typescript
interface RegisterFormProps {
  onSuccess?: () => void;
}
```

**Usage:**
```tsx
import { RegisterForm } from '@/components/auth/RegisterForm';

<RegisterForm onSuccess={() => navigate('/dashboard')} />
```

**Features:**
- Multi-field validation
- Password confirmation
- Role selection (student/teacher)
- Zod validation schema
- Loading states

**Form Fields:**
- Name (required)
- Email (required, valid email)
- Password (required, min 8 chars)
- Confirm Password (must match)
- Role (student or teacher)

---

## Challenge Components

### ChallengeCard

Displays a single challenge with completion status.

**Location:** `src/components/challenge/ChallengeCard.tsx`

**Props:**
```typescript
interface ChallengeCardProps {
  challenge: Challenge;
  onClick?: () => void;
  showProgress?: boolean;
}

interface Challenge {
  unit_id: number;
  challenge_id: number;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  points: number;
  completed: boolean;
  user_points_earned?: number;
  attempts?: number;
}
```

**Usage:**
```tsx
import { ChallengeCard } from '@/components/challenge/ChallengeCard';

<ChallengeCard
  challenge={challenge}
  onClick={() => navigate(`/challenges/${challenge.unit_id}/${challenge.challenge_id}`)}
  showProgress={true}
/>
```

**Features:**
- Completion checkmark
- Difficulty badge
- Points display
- Attempt count
- Hover effects
- Click to open

**Visual States:**
- Completed: Green checkmark, full opacity
- In Progress: Partial progress indicator
- Not Started: Gray, muted

---

### SchemaView

Database schema viewer for challenges.

**Location:** `src/components/challenge/SchemaView.tsx`

**Props:**
```typescript
interface SchemaViewProps {
  schema: DatabaseSchema;
  collapsible?: boolean;
}

interface DatabaseSchema {
  tables: {
    name: string;
    columns: {
      name: string;
      type: string;
      nullable?: boolean;
    }[];
  }[];
}
```

**Usage:**
```tsx
import { SchemaView } from '@/components/challenge/SchemaView';

<SchemaView
  schema={{
    tables: [
      {
        name: 'users',
        columns: [
          { name: 'id', type: 'INTEGER', nullable: false },
          { name: 'name', type: 'TEXT', nullable: false },
          { name: 'email', type: 'TEXT', nullable: false }
        ]
      }
    ]
  }}
  collapsible={true}
/>
```

**Features:**
- Collapsible tables
- Column type indicators
- Nullable indicators
- Syntax highlighting

---

### HintSystem

Multi-level hint system with point penalties.

**Location:** `src/components/challenge/HintSystem.tsx`

**Props:**
```typescript
interface HintSystemProps {
  unitId: number;
  challengeId: number;
  onHintAccessed?: (penalty: number) => void;
}
```

**Usage:**
```tsx
import { HintSystem } from '@/components/challenge/HintSystem';

<HintSystem
  unitId={1}
  challengeId={1}
  onHintAccessed={(penalty) => console.log(`-${penalty} points`)}
/>
```

**Features:**
- Progressive hints (level 1, 2, 3)
- Point penalty warnings
- Unlock hints sequentially
- Accessed hint tracking
- Confirmation dialogs

**Hint Levels:**
- Level 1: Small hint, -10 points
- Level 2: Medium hint, -20 points
- Level 3: Detailed hint, -50 points

---

### ExpectedOutput

Shows the expected query output for a challenge.

**Location:** `src/components/challenge/ExpectedOutput.tsx`

**Props:**
```typescript
interface ExpectedOutputProps {
  output: QueryResult;
  showQuery?: boolean;
}

interface QueryResult {
  columns: string[];
  rows: any[][];
}
```

**Usage:**
```tsx
import { ExpectedOutput } from '@/components/challenge/ExpectedOutput';

<ExpectedOutput
  output={{
    columns: ['id', 'name', 'email'],
    rows: [
      [1, 'John Doe', 'john@example.com'],
      [2, 'Jane Smith', 'jane@example.com']
    ]
  }}
  showQuery={false}
/>
```

---

## Query Components

### QueryEditor

SQL query editor with syntax highlighting.

**Location:** `src/components/query/QueryEditor.tsx`

**Props:**
```typescript
interface QueryEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  disabled?: boolean;
  placeholder?: string;
}
```

**Usage:**
```tsx
import { QueryEditor } from '@/components/query/QueryEditor';
import { useState } from 'react';

function ChallengeEditor() {
  const [query, setQuery] = useState('');

  return (
    <QueryEditor
      value={query}
      onChange={setQuery}
      onSubmit={handleSubmit}
      placeholder="Enter your SQL query..."
    />
  );
}
```

**Features:**
- SQL syntax highlighting
- Line numbers
- Auto-indentation
- Ctrl+Enter to submit
- Tab support
- Undo/redo

---

### QueryResult

Displays query execution results.

**Location:** `src/components/query/QueryResult.tsx`

**Props:**
```typescript
interface QueryResultProps {
  result: {
    columns: string[];
    rows: any[][];
    rowCount: number;
    executionTime?: number;
  };
  isCorrect?: boolean;
}
```

**Usage:**
```tsx
import { QueryResult } from '@/components/query/QueryResult';

<QueryResult
  result={{
    columns: ['name', 'email'],
    rows: [['John Doe', 'john@example.com']],
    rowCount: 1,
    executionTime: 12
  }}
  isCorrect={true}
/>
```

**Features:**
- Tabular result display
- Row count indicator
- Execution time
- Success/error styling
- Empty result handling

---

## Progress Components

### ProgressCard

Displays user progress statistics.

**Location:** `src/components/progress/ProgressCard.tsx`

**Props:**
```typescript
interface ProgressCardProps {
  progress: {
    total_points: number;
    challenges_completed: number;
    total_challenges: number;
    completion_rate: number;
  };
}
```

**Usage:**
```tsx
import { ProgressCard } from '@/components/progress/ProgressCard';

<ProgressCard
  progress={{
    total_points: 450,
    challenges_completed: 5,
    total_challenges: 7,
    completion_rate: 71.43
  }}
/>
```

**Features:**
- Points display
- Completion percentage
- Progress bar
- Challenge count
- Achievement badges

---

### ProgressChart

Visual progress chart (line/bar chart).

**Location:** `src/components/progress/ProgressChart.tsx`

**Props:**
```typescript
interface ProgressChartProps {
  data: {
    date: string;
    points: number;
    challenges: number;
  }[];
  type?: 'line' | 'bar';
}
```

**Usage:**
```tsx
import { ProgressChart } from '@/components/progress/ProgressChart';

<ProgressChart
  data={[
    { date: '2025-11-10', points: 100, challenges: 1 },
    { date: '2025-11-15', points: 250, challenges: 3 }
  ]}
  type="line"
/>
```

**Features:**
- Recharts integration
- Responsive
- Tooltips
- Interactive legends
- Multiple data series

---

## Leaderboard Components

### LeaderboardTable

Displays the leaderboard rankings.

**Location:** `src/components/leaderboard/LeaderboardTable.tsx`

**Props:**
```typescript
interface LeaderboardTableProps {
  leaderboard: {
    rank: number;
    user_id: number;
    name: string;
    total_points: number;
    challenges_completed: number;
  }[];
  currentUserId?: number;
  showRank?: number; // Highlight specific rank
}
```

**Usage:**
```tsx
import { LeaderboardTable } from '@/components/leaderboard/LeaderboardTable';

<LeaderboardTable
  leaderboard={leaderboardData}
  currentUserId={user.id}
  showRank={10}
/>
```

**Features:**
- Rank badges (1st, 2nd, 3rd)
- Current user highlighting
- Points and completion display
- Responsive design
- Pagination support

---

## Teacher Components

### StudentList

List of students with search and filters.

**Location:** `src/components/teacher/StudentList.tsx`

**Props:**
```typescript
interface StudentListProps {
  students: Student[];
  onStudentClick?: (student: Student) => void;
  searchable?: boolean;
  sortable?: boolean;
}
```

**Usage:**
```tsx
import { StudentList } from '@/components/teacher/StudentList';

<StudentList
  students={students}
  onStudentClick={(student) => navigate(`/teacher/students/${student.id}`)}
  searchable={true}
  sortable={true}
/>
```

**Features:**
- Search by name/email
- Sort by name, points, completion
- Click to view details
- Pagination
- Loading states

---

### AnalyticsDashboard

Class analytics dashboard.

**Location:** `src/components/teacher/AnalyticsDashboard.tsx`

**Props:**
```typescript
interface AnalyticsDashboardProps {
  analytics: ClassAnalytics;
  refreshInterval?: number;
}
```

**Usage:**
```tsx
import { AnalyticsDashboard } from '@/components/teacher/AnalyticsDashboard';

<AnalyticsDashboard
  analytics={analyticsData}
  refreshInterval={60000} // 1 minute
/>
```

**Features:**
- Overview stats cards
- Challenge completion charts
- Top performers list
- Struggling students alerts
- Auto-refresh

---

### StudentDetailView

Detailed view of individual student progress.

**Location:** `src/components/teacher/StudentDetailView.tsx`

**Props:**
```typescript
interface StudentDetailViewProps {
  studentId: number;
  showProgress?: boolean;
  showAttempts?: boolean;
}
```

**Usage:**
```tsx
import { StudentDetailView } from '@/components/teacher/StudentDetailView';

<StudentDetailView
  studentId={1}
  showProgress={true}
  showAttempts={true}
/>
```

**Features:**
- Student info card
- Progress timeline
- Challenge attempts
- Hint usage
- Export student data

---

## Navigation Components

### Navigation

Main navigation bar.

**Location:** `src/components/navigation/Navigation.tsx`

**Props:**
```typescript
interface NavigationProps {
  // No props - uses AuthContext
}
```

**Usage:**
```tsx
import { Navigation } from '@/components/navigation/Navigation';

// In App.tsx
<Navigation />
```

**Features:**
- Responsive (mobile hamburger menu)
- Role-based links (student vs teacher)
- User dropdown menu
- Logout button
- Active route highlighting

**Navigation Links:**
- Students: Dashboard, Challenges, Leaderboard, Progress
- Teachers: Dashboard, Students, Analytics, Import

---

## Routing Components

### ProtectedRoute

Requires authentication to access.

**Location:** `src/components/routing/ProtectedRoute.tsx`

**Props:**
```typescript
interface ProtectedRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}
```

**Usage:**
```tsx
import { ProtectedRoute } from '@/components/routing/ProtectedRoute';

<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <DashboardPage />
    </ProtectedRoute>
  }
/>
```

**Behavior:**
- Redirects to `/login` if not authenticated
- Preserves intended destination for post-login redirect

---

### RoleProtectedRoute

Requires specific role to access.

**Location:** `src/components/routing/RoleProtectedRoute.tsx`

**Props:**
```typescript
interface RoleProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles: ('student' | 'teacher')[];
  redirectTo?: string;
}
```

**Usage:**
```tsx
import { RoleProtectedRoute } from '@/components/routing/RoleProtectedRoute';

<Route
  path="/teacher/*"
  element={
    <RoleProtectedRoute allowedRoles={['teacher']}>
      <TeacherDashboard />
    </RoleProtectedRoute>
  }
/>
```

**Behavior:**
- Redirects to `/unauthorized` if wrong role
- Requires authentication first

---

## Provider Components

### ToastProvider

Toast notification provider using Sonner.

**Location:** `src/components/providers/ToastProvider.tsx`

**Usage:**
```tsx
import { ToastProvider } from '@/components/providers/ToastProvider';
import { toast } from 'sonner';

// In App.tsx
<ToastProvider>
  <App />
</ToastProvider>

// In components
toast.success('Challenge completed!');
toast.error('Submission failed');
toast.info('Hint accessed');
```

**Toast Types:**
- `toast.success()` - Green checkmark
- `toast.error()` - Red error
- `toast.info()` - Blue info
- `toast.warning()` - Yellow warning

---

## Component Best Practices

### Naming Conventions

```tsx
// Component files: PascalCase
LoginForm.tsx
ChallengeCard.tsx

// Component exports: Named exports
export function LoginForm() { }
export function ChallengeCard() { }

// NOT default exports
// export default LoginForm; ❌
```

### Props Pattern

```tsx
// Use TypeScript interfaces for props
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
}

export function Button({ children, onClick, variant = 'primary' }: ButtonProps) {
  // Implementation
}
```

### Component Structure

```tsx
// 1. Imports
import { useState } from 'react';
import { Button } from '@/components/ui/Button';

// 2. Types/Interfaces
interface ComponentProps {
  // ...
}

// 3. Component
export function Component({ prop1, prop2 }: ComponentProps) {
  // 3a. Hooks
  const [state, setState] = useState();

  // 3b. Handlers
  const handleClick = () => {
    // ...
  };

  // 3c. Effects
  useEffect(() => {
    // ...
  }, []);

  // 3d. Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

### Accessibility

```tsx
// Always include ARIA labels
<button aria-label="Close modal" onClick={onClose}>
  <X />
</button>

// Use semantic HTML
<nav>
  <ul>
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>

// Keyboard navigation
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => e.key === 'Enter' && onClick()}
>
  Click me
</div>
```

### Performance

```tsx
// Memoize expensive components
const MemoizedChart = React.memo(ProgressChart);

// Use callbacks to prevent re-renders
const handleSubmit = useCallback(() => {
  // ...
}, [dependencies]);

// Lazy load routes
const TeacherDashboard = lazy(() => import('./pages/teacher/Dashboard'));
```

### Testing

```tsx
// Component tests with Vitest + Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

---

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md) - System architecture and design patterns
- [API Reference](API.md) - Backend API documentation
- [Frontend README](../frontend/README.md) - Frontend development guide

---

*Last updated: 2025-11-17*
